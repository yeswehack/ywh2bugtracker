.DEFAULT_GOAL := help

FLAKE8_SRCS := ywh2bt/core ywh2bt/cli ywh2bt/gui ywh2bt/__init__.py ywh2bt/version.py stubs
MYPY_SRCS := ywh2bt stubs
DOCKER_TAG := ywh2bt

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
	@poetry install --no-root

.PHONY: update-gui-resources-file
update-gui-resources-file:  ## update the GUI resources file (qrc)
	@poetry run python ywh2bt/gui/update_resources_file.py

.PHONY: compile-gui-resources
compile-gui-resources: update-gui-resources-file _install_no_root  ## compile the GUI resources
	@poetry run pyside2-rcc ywh2bt/gui/resources.qrc -o ywh2bt/gui/resources.py

.PHONY: build
build: compile-gui-resources  ## build the project
	@poetry build

.PHONY: install
install:  ## install the project locally
	@poetry install

.PHONY: tests
tests: _install_no_root ## run the tests with the current python interpreter
	@poetry run python -m unittest discover -s ywh2bt/tests -v

.PHONY: tox
tox: _install_no_root ## run the tests using tox
	@poetry run tox

.PHONY: mypy
mypy: ## check typing using mypy
	@mkdir -p build/mypy
	@poetry run mypy \
		--html-report build/mypy \
		$(MYPY_SRCS)

.PHONY: flake8
flake8: ## check code violations using flake8
	@mkdir -p build/flake8
	@poetry run flake8 \
		--format=html \
		--htmldir=build/flake8 \
		$(FLAKE8_SRCS)

.PHONY: build-docker
build-docker: ## build the docker image
	@docker build --tag $(DOCKER_TAG) .
