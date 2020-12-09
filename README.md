# ywh2bt

ywh2bt allows you to integrate your bug tracking system(s) with [YesWeHack platform](https://www.yeswehack.com/).
It automatically creates issues in your bug tracking system for all your program's report,
and add to the concerned reports the link to the issue.

Currently github, jira/jiracloud and gitlab are supported.

## Requirements

- `python` >= 3.7
- [`pip`](https://pip.pypa.io/en/stable/installing/)

## Installation

```sh
pip install ywh2bt
```

## Provided scripts

### `ywh2bt`

The main script used to execute synchronization, validate and test configurations.

Usage: `ywh2bt [command]`. See `ywh2bt -h` or `ywh2bt [command] -h` for detailed help.

#### Commands

- `validate`: validate a configuration file (mandatory fields, data types, ...)
- `test`: test the connection to the trackers
- `convert`: convert a configuration file into another format
- `synchronize` (alias `sync`): synchronize trackers with YesWeHack reports
- `schema`: dump a schema of the structure of the configuration files in [Json-Schema][Json-Schema], markdown or plaintext

##### Example usages

Validation:
```sh
$ ywh2bt validate \
    --config-file=my-config.yml \
    --config-format=yaml && echo OK
OK
```

Conversion (`yaml` to `json`):
```sh
$ ywh2bt convert \
    --config-file=my-config.yml \
    --config-format=yaml \
    --destination-file=/tmp/cfg.json \
    --destination-format=json
```

Synchronization:
```sh
$ ywh2bt synchronize --config-file=my-config.json --config-format=json
Starting synchronization:
  Sending report #123 'CVE-2017-11882 on program' to github: OK (https://github.com/user/project/issues/420).
  Sending report #96 'I found a bug' to gitlab: OK (https://gitlab.com/example/ywh2bt/-/issues/987).
Synchronization done.
```

#### Supported configuration file formats

- `yaml` (legacy)
- `json`

Use `ywh2bt schema -f json` to obtain a [Json-Schema][Json-Schema] describing the format.
Both `yaml` and `json` configuration files should conform to the schema. 

#### Configuration note

Apps API doesn't require TOTP authentication, even if corresponding user has TOTP enabled.

However, on a secured program, information is limited for user with TOTP disabled, even in apps.

As a consequence, to allow proper bug tracking integration on a secured program,
program consumer must have TOTP enabled and, in BTI configuration TOTP must be set to `false`.

### `ywh2bt-gui`

A script that launches a GUI to create and edit configurations, and execute synchronizations.

Usage: `ywh2bt-gui`.

## Local development

### Requirements

- [`poetry`](https://python-poetry.org/) (`pip install poetry`)

### Installation

- `make install` (or `poetry install`): creates a virtualenv and install dependencies

### Usage

Instead of `ywh2bt [command]`, run commands using `poetry run ywh2bt [command]`.

Same goes for `ywh2bt-gui`, run `poetry run ywh2bt-gui` instead.


[Json-Schema]: https://json-schema.org/specification.html