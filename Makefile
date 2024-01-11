.DEFAULT_GOAL := help

MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(patsubst %/,%,$(dir $(MAKEFILE_PATH)))

SRCS := ywh2bt
FLAKE8_SRCS := ywh2bt/core ywh2bt/cli ywh2bt/gui ywh2bt/*.py stubs
MYPY_SRCS := ywh2bt stubs
DOCKER_TAG := ywh2bt
PANDOC_DOCKER_IMAGE := pandoc-extended:latest
POPPLER_DOCKER_IMAGE := minidocks/poppler:latest

USER_GUIDE_MD5SUM := `md5sum docs/User-Guide.md | cut -d' ' -f1`
USER_GUIDE_BUILD_PATH := docs/user-guide

.PHONY: help
help:  ## show this help
	@grep -E '^[a-zA-Z1-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-30s - %s\n", $$1, $$2}'

.PHONY: clean
clean:  ## clean the project
	@rm -rf build dist .eggs *.egg-info
	@rm -rf .benchmarks .coverage coverage.xml htmlcov report.xml .tox
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -exec rm -rf {} +

.PHONY: _install_no_root
_install_no_root:
	@poetry install --no-root --all-extras

.PHONY: update-gui-resources-file
update-gui-resources-file:  ## update the GUI resources file (qrc)
	@poetry run python ywh2bt/gui/update_resources_file.py

.PHONY: compile-gui-resources
compile-gui-resources: update-gui-resources-file _install_no_root  ## compile the GUI resources
	@poetry run pyside6-rcc ywh2bt/gui/resources.qrc -o ywh2bt/gui/resources.py

.PHONY: build
build: compile-gui-resources  ## build the project
	@poetry build

.PHONY: install
install:  ## install the project locally
	@poetry run pip uninstall --yes ywh2bt
	@poetry install

.PHONY: install-with-gui
install-with-gui:  ## install the project locally, including the gui
	@poetry run pip uninstall --yes ywh2bt
	@poetry install --extras=gui

.PHONY: tests
tests: _install_no_root ## run the tests with the current python interpreter
	@poetry run python -m ywh2bt.tests.main

.PHONY: tox
tox: _install_no_root ## run the tests using tox
	@poetry run tox run-parallel -vvv

.PHONY: typing mypy
typing: _install_no_root ## check typing using mypy
	@echo >&2 "Checking types with mypy (`poetry run dmypy --version`)"...
	@poetry run dmypy stop || true  # stopping dmypy until https://github.com/python/mypy/issues/9655 is fixed
	@poetry run dmypy run $(MYPY_SRCS)
mypy: typing

.PHONY: lint flake8
lint: _install_no_root ## check code violations using flake8
	@echo >&2 "Linting with flake8... (`poetry run flake8 --version | tr '\n' ' '`)"
	@poetry run flake8 $(FLAKE8_SRCS)
flake8: lint

.PHONY: format
format: ## format source code using isort/black
	@echo >&2 Formatting with black...
	@poetry run isort $(SRCS)
	@poetry run black $(SRCS)

.PHONY: format-check
format-check: ## check source code formatting using isort/black
	@poetry run isort --check $(SRCS)
	@poetry run black --check $(SRCS)

.PHONY: build-docker
build-docker: ## build the docker image
	@docker build --tag $(DOCKER_TAG) .

.PHONY: _pandoc-extended
_pandoc-extended:
	@cd docs/pandoc && \
	docker build \
		--quiet \
		--tag $(PANDOC_DOCKER_IMAGE) \
		--file Dockerfile \
		. >/dev/null

.PHONY: user-guide
user-guide: user-guide-html user-guide-pdf ## create all the versions of the User Guide

.PHONY: user-guide-html
user-guide-html: _pandoc-extended ## create the HTML version of the User Guide
	@mkdir -p $(USER_GUIDE_BUILD_PATH)
	@docker run \
		--rm \
		--user `id -u`:`id -g` \
		--volume "/$(MAKEFILE_DIR)/docs:/docs" \
		--volume "/$(MAKEFILE_DIR)/$(USER_GUIDE_BUILD_PATH):/$(USER_GUIDE_BUILD_PATH)" \
		--workdir /docs \
		$(PANDOC_DOCKER_IMAGE) \
		--defaults=User-Guide-defaults-html.yaml \
		--metadata=keywords:md5sum=$(USER_GUIDE_MD5SUM) \
		--output=/$(USER_GUIDE_BUILD_PATH)/User-Guide.html

.PHONY: user-guide-pdf
user-guide-pdf: _pandoc-extended ## create the PDF version of the User Guide
	@mkdir -p $(USER_GUIDE_BUILD_PATH)
	@docker run \
		--rm \
		--user `id -u`:`id -g` \
		--volume "/$(MAKEFILE_DIR)/docs:/docs" \
		--volume "/$(MAKEFILE_DIR)/$(USER_GUIDE_BUILD_PATH):/$(USER_GUIDE_BUILD_PATH)" \
		--workdir /docs \
		$(PANDOC_DOCKER_IMAGE) \
		--defaults=User-Guide-defaults-pdf.yaml \
		--metadata=keywords:md5sum=$(USER_GUIDE_MD5SUM) \
		--output=/$(USER_GUIDE_BUILD_PATH)/User-Guide.pdf

.PHONY: user-guide-md5sum-html
user-guide-md5sum-html:  ## extract MD5sum of original User-Guide.md from generated HTML
		@docker run \
		--rm \
		--user `id -u`:`id -g` \
		--volume "/$(MAKEFILE_DIR)/$(USER_GUIDE_BUILD_PATH):/$(USER_GUIDE_BUILD_PATH)" \
		--workdir /$(USER_GUIDE_BUILD_PATH) \
		pipelinecomponents/xmllint \
		xmllint \
		--html \
		--xpath 'string(/html/head/meta[@name="keywords"]/@content)' \
		User-Guide.html 2>/dev/null | sed -E 's/.*md5sum=([0-9a-f]{32}).*/\1/'

.PHONY: user-guide-md5sum-pdf
user-guide-md5sum-pdf: ## extract MD5sum of original User-Guide.md from generated PDF
	@docker run \
		--rm \
		--volume "/$(MAKEFILE_DIR)/docs/bin/noop.sh:/docker-entrypoint.d/05-certificates.sh" \
		--volume "/$(MAKEFILE_DIR)/$(USER_GUIDE_BUILD_PATH):/$(USER_GUIDE_BUILD_PATH)" \
		--workdir /$(USER_GUIDE_BUILD_PATH) \
		$(POPPLER_DOCKER_IMAGE) \
		pdfinfo User-Guide.pdf | \
		grep 'Keywords:' | sed -E 's/.*md5sum=([0-9a-f]{32}).*/\1/' | tr -d '\n'

.PHONY: user-guide-md5sum-markdown
user-guide-md5sum-markdown:  ## get MD5sum of User-Guide.md
	@echo -n $(USER_GUIDE_MD5SUM)
