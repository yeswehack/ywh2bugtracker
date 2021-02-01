# YWH2BT

YesWeHack <-> bug tracker synchronization tool.

- [Features](#features)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
    - [GUI](#gui)
        - [Screenshots](#screenshots)
        - [A few tips](#a-few-tips)
    - [Command line](#command-line)
        - [Examples](#examples)
- [Supported trackers](#supported-trackers)
- [Supported configuration file formats](#supported-configuration-file-formats)
- [Known limitations and specific behaviours](#known-limitations-and-specific-behaviours)
- [Changelog](#changelog)
- [Local development](#local-development)
    - [Requirements](#requirements-1)
    - [Installation](#installation-1)
    - [Usage](#usage-1)

## Features

YWH2BT provide synchronization between [YesWeHack platform][YesWeHack-Platform] platform and your organization's bug tracker(s):
platform reports and related information (comments, attachments...) are automatically copied to your bug tracker(s),
while completely controlling the information you allow to be copied.

It comes with a handy GUI to set up and test the integration.

## Architecture

YWH2BT embeds both the GUI to set up the integration,
and the application to be scheduled on your server to periodically poll and synchronize new reports.  
You can either run both on a single machine, or prepare the configuration file
on a computer (with the GUI) and transfer it on the server and use it through a scheduled command.

Since data is pulled from YWH platform to your server, only regular outbound web connections need to be authorized on your server.

## Requirements

- `python` >= 3.7,<=3.9
- [`pip`](https://pip.pypa.io/en/stable/installing/)

## Installation

YWH2BT can be installed with `pip`, through the command:
```sh
pip install ywh2bt
```

If you need to deploy only the command line version on a server, a runnable docker image is also available.
You can install it with:
```sh
docker pull yeswehack/ywh2bugtracker:latest
```
Then, run it with the same command as described [below](#command-line), prefixed with `docker run yeswehack/ywh2bugtracker`.   
See `docker run yeswehack/ywh2bugtracker -h` or `docker run yeswehack/ywh2bugtracker [command] -h` for detailed help.

## Usage

### GUI

The GUI provides assistance to create, modify and validate/test configurations. 
It also allows synchronization with bug trackers.

To run it, simply type `ywh2bt-gui` in a shell.

#### Screenshots

- [example.yml](doc/examples/example.yml) configuration:

![Screenshot of GUI with loaded example file](doc/img/screenshot-gui-example.png)

- [empty configuration](doc/img/screenshot-gui-new.png)

#### A few tips

- Changes to the configuration can be made either in the configuration tab or in the "Raw" tab ; 
  changes made in one tab are automatically reflected in the other tab.
- Hovering labels and buttons with the mouse pointer often reveals more information in a floating tooltip 
  or in the status bar.
- A description of the schema of the configuration files is accessible via the "Help > Schema documentation" menu
  or by clicking on the ![Icon for help button](doc/img/icon-help.png) button in the main toolbar.

### Command line

The main script `ywh2bt` is used to execute synchronization, validate and test configurations.

Usage: `ywh2bt [command]`.  
See `ywh2bt -h` or `ywh2bt [command] -h` for detailed help.

Where `[command]` can be:
- `validate`: validate a configuration file (mandatory fields, data types, ...)
- `test`: test the connection to the trackers
- `convert`: convert a configuration file into another format
- `synchronize` (alias `sync`): synchronize trackers with YesWeHack reports. It should be run everytime you want to synchronize (e.g. schedule execution in a crontab).
- `schema`: dump a schema of the structure of the configuration files in [Json-Schema][Json-Schema], markdown 
  or plaintext

#### Examples

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
[2020-12-21 10:20:58.881315] Starting synchronization:
[2020-12-21 10:20:58.881608]   Processing YesWeHack "yeswehack1":
[2020-12-21 10:20:58.881627]     Fetching reports for program "my-program": 2 report(s)
[2020-12-21 10:21:08.341460]     Processing report #123 (CVE-2017-11882 on program) with "my-github": https://github.com/user/project/issues/420 (untouched ; 0 comment(s) added) | tracking status unchanged
[2020-12-21 10:21:09.656178]     Processing report #96 (I found a bug) with "my-github": https://github.com/user/project/issues/987 (created ; 3 comment(s) added) | tracking status updated
[2020-12-21 10:21:10.773688] Synchronization done.
```

Synchronization through docker:
```sh
$ docker run \
    --volume /home/dave/config/my-config.json:/ywh2bt/config/my-config.json \
    --network host \
    yeswehack/ywh2bugtracker:latest \
    sync --config-file=/ywh2bt/config/my-config.json --config-format=json
[2020-12-21 11:20:58.881315] Starting synchronization:
[2020-12-21 11:20:58.881608]   Processing YesWeHack "yeswehack1":
[2020-12-21 11:20:58.881627]     Fetching reports for program "my-program": 2 report(s)
[2020-12-21 11:21:08.341460]     Processing report #123 (CVE-2017-11882 on program) with "my-github": https://github.com/user/project/issues/420 (untouched ; 0 comment(s) added) | tracking status unchanged
[2020-12-21 11:21:09.656178]     Processing report #96 (I found a bug) with "my-github": https://github.com/user/project/issues/987 (created ; 3 comment(s) added) | tracking status updated
[2020-12-21 11:21:10.773688] Synchronization done.
```

## Supported trackers

- github
- gitlab
- jira / jiracloud

## Supported configuration file formats

- `yaml` (legacy)
- `json`

Use `ywh2bt schema -f json` to obtain a [Json-Schema][Json-Schema] describing the format.
Both `yaml` and `json` configuration files should conform to the schema. 

## Known limitations and specific behaviours

- This tool requires you to have "Use Apps API" right on [YesWeHack platform][YesWeHack-Platform],
  and a custom HTTP header value to put in your configuration.
  Both of them can be obtained by e-mailing us at support@yeswehack.com.
- Apps API doesn't require TOTP authentication, even if corresponding user has TOTP enabled.  
  However, on a secured program, information is limited for user with TOTP disabled, even in apps.  
  As a consequence, to allow proper bug tracking integration on a secured program,
  program consumer must have TOTP enabled and, in BTI configuration TOTP must be set to `false`.
- References to a same uploaded attachment in different comments is not supported yet,
  i.e., if an attachment is referenced (either displayed inline or as a link) in several comments,
  only first one will be correctly handled.
- Manually tracked reports (i.e., where a manager directly set the Tracking status to "tracked") 
  are also integrated in the tracker the way they are when a manager set "Ask for integration".
- Since v2.0.0, unlike in previous versions, setting a tracked report back to "Ask for integration" 
  won't create a new issue in the tracker but update the existing one.

## Changelog

- v0.* to v2.0.0:
    - behavior changes:
        - reports logs can selectively be synchronized with the trackers:
            - public comments
            - private comments
            - report details changes
            - report status changes
            - rewards
        - a program can now only be synchronized with 1 tracker
    - added support for JSON configuration files
    - removed `ywh-bugtracker` command (use `ywh2bt synchronize`)
    - added `ywh2bt` command:
        - added `ywh2bt synchronize`:
            - note: `ywh2bt synchronize --config-file FILE --config-format FORMAT` 
              is the equivalent of `ywh-bugtracker -n -f FILE` in v0.*
        - added `ywh2bt validate`
        - added `ywh2bt test`
        - added `ywh2bt convert`
        - added `ywh2bt schema`
    - removed command line interactive mode
    - added GUI via `ywh2bt-gui` command

## Local development

### Requirements

- [`poetry`](https://python-poetry.org/) (`pip install poetry`)

### Installation

- `make install` (or `poetry install`): creates a virtualenv and install dependencies

### Usage

Instead of `ywh2bt [command]`, run commands using `poetry run ywh2bt [command]`.

Same goes for `ywh2bt-gui`, run `poetry run ywh2bt-gui` instead.


[YesWeHack-Platform]: https://www.yeswehack.com/
[Json-Schema]: https://json-schema.org/specification.html
[Docker-Repository]: https://hub.docker.com/r/yeswehack/ywh2bugtracker