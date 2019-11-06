# What is that ?

ywh2bugtracker allows you to integrate your bug tracking system(s) with yeswehack platform. It automatically creates issues in your bug tracking system for all your program's report with tracking status "Ask for integration", and add to the concerned reports the link to the issue in your bugtracker . Currently github, jira and gitlab are supported, and you can add your own bug tracker by following instructions [below](#Create-Your-Config-Manager-Object).


# Installation

installation is available from pip for windows, linux, mac OS.

```
pip install ywh2bt
```

# Usage

a simple commande is available:

```
ywh-bugtracker {options}
```

Options:
- -n --no-interactive: Non interactive mode.
    * With -c options: all configure data are stored in the configuration file (included credencials).
    * Without -c options: one test is used at load time to see if credencials exists. if not, a critical error is logged to know the specific credential missing.
- -c --configure: Configuration mode.
    *  Interactive system to configure or modify configuration file.
    *  At load time, if an existing configuration file exists, it is loaded and verified.
    *  You can add new element in configuration file and, a the tend, you can modify your existings elements.
- -f --filename <filename>: given specified configuration file (default : HOME/.ywh2bt.cfg).

## Configuration File

A ywh2bt configuration file is a yaml describing each element and interaction between them.

This file have 3 goals :
- Setup bugtracker system (Bugtracker-s issue-s client-s and YesWeHack-s Client-s).
- Define configuration for the necessary interactions with Yeswehack APIs 
- Append Extra bugtrackers class to this system if needed

Example of typical configuration file:

```yaml
bugtrackers:
  jira:
    issuetype: Task
    login: user
    password: password_user
    project: myprojectonjira
    type: jira
    url: http://myjira.com
  github:
    project: path/to/myprojectongithub
    token: myaccesstoken
    type: github
    url: https://github/api/v3
  gitlab:
    project: path/to/myproject
    token: mygitlabtoken
    type: gitlab
    url: gitlab_valid_url
  myissuelogger:
    project: myprojectonmyissuelogger
    assigned_to: user_name_to_assign_issue
    login: user_login
    token: myaccesstoken
    type: myissuelogger
    url: http://myissuelogger.com/
yeswehack:
  yeswehack_1:
    api_url: https://api.yeswehack.com
    login: mylogintoyeswehack@yeswehack.com
    password: password_login
    programs:
    - bugtrackers_name:
      - gitlab
      - github
      - jira
      - myissuelogger
      slug: myproject
    totp: false
    apps_headers:
      X-YesWeHack-Apps: ywh_app_header
    oauth_args:
      client_id: apps_client_id
      client_secret: apps_client_secrect
      redirect_uri: apps_redirect_uri
packages:
- modules:
  - ywhmyissuelogger
  package: myissueloggerconfig
  path: ../../myissuelogger
```

On this configuration file, we define three bugtrackers :
- The first three items ('jira', 'gitlab' and 'github'), are proposed and maintained by YesWeHack.
- The last one ('myissuelogger'), is an example of use of a third party development handling another bug tracking system, not supported by ywh2bt. The  `packages` section defines python module to include for management of abug trackers and the parameters of this module. You can see more information about create your own config object and include it in [this section](#Create-Your-Config-Manager-Object).


### Setup bugtracker System

In this section we explain the "bugtrackers" part, and how to configure each type of bugtrackers supported by YesWeHack.

As you can see on the example below, we proposed three type of bugtrackers by default. Each of them have some attribute,
each attribute can be mandatory, optional (github url for example), or secret (an access token).

```yaml
bugtrackers:
  jira:
    issuetype: Task
    login: user
    password: password_user
    project: projectname
    type: jira
    url: http://myjira.com
  github:
    project: path/to/my/project/on/github
    token: myaccesstoken
    type: github
    url: https://github/api/v3
  gitlab:
    project: path/to/my/project/on/mygitlab
    token: myaccesstoken
    type: gitlab
    url: http://local.gitlab.com/
```

#### Bugtrackers Object

Each of the bugtrackers have a silent mandatory attribute named type and corresping to the bugtracker type (i.e. type=jira for jira bugtracker), and an identifiant name, set automatically in configuration mode (bugtracker_number).

Secret keys are needed in configuration file on no interactive mode, otherwise, it is ask interactively.

Jira:
- mandatory keys:
    * url: url to your jira installation
    * login: user login to set the issue, the user must have sufficient right to push the issue on jira project.
    * project: project slug which have the issue on it.
- optional keys:
    * issuetype (default 'Task'): type of the issue, by default we consider 'Task', but it could have an other name (depend of jira language installation).
- secret keys:
    * password: password for the user login set.

Gitlab:
- mandatory keys:
    * project: path/of/the/project. If the project is in a group named 'projectsgroups', and the project name is 'test', your project is 'projectsgroups/test'
- optional keys:
    * url (default 'http://gitlab.com'): url to your gitlab installation
- secret keys:
    * token: user token to push the issue on your gitlab. the user and the token need to have sufficient rights to push the issue on the project.

Github:
- mandatory keys:
    * project: github repository path to your project. If my name is 'BugTracker' and my 'project' is example, my repository path is 'BugTracker/project'
- optional keys:
    * url (default 'https://github/api/v3'): url to github api access, by default, we used the V3 api url.
- secret keys:
    * token: user token to push the issue on github. the user and the token need to have sufficient rights to push the issue on the project.


#### YesWeHack Object

YesWeHack configuration part define one or more yeswehack object:

```yaml
yeswehack:
  yeswehack_1:
    api_url: https://api.yeswehack.com
    login: mylogintoyeswehack@yeswehack.com
    password: password_login
    totp: false
    programs:
    - bugtrackers_name:
      - bugtracker_3
      slug: myproject
  yeswehack_2:
    api_url: https://api.yeswehack.com
    login: myotherlogintoyeswehack@yeswehack.com
    password: otherpassword_login
    apps_headers:
      X-YesWeHack-Apps: ywh_app_header
    oauth_args:
      client_id: apps_client_id
      client_secret: apps_client_secrect
      redirect_uri: apps_redirect_uri
    programs:
    - bugtrackers_name:
      - bugtracker_1
      - bugtracker_3
      slug: myproject_api
    - bugtrackers_name:
      - bugtracker_2
      slug: anotherproject
    totp: True
    totp_secret: mytopt
```

YesWeHack Object:
- mandatory keys
  * apps_headers: headers to update reports in YesWeHack program.
  * api_url: url to YesWeHack api
  * login: my user Login . **NB : This user must have program consumer role on the program** 
  * totp: if totp is enable on for my user.
  * totp_secret: needed in configuration file only if totp is True and in no interactive mode.
  * programs (list of item):
    * bugtrackers_name: bugtrackers names defined in ["Setup bugtracker System" section](#Setup-bugtracker-System).
    * slug: program slug (found in th url of your program)
  * oauth_args: (object)
    * client_id: client_id for the app
    * client_secret: client_id for the app (in no interactive mode)
    * redirect_uri : redirect_uri for the app

- secret keys:
  * password: my user password


## Append Extra BugTracker class

To Allow you to add your own bugtracker an easy way, we have defined a packages section in the configuration file.
You just have to create a python package-s/module-s with your bugtracker python class define in it/them.

```yaml
packages:
- modules:
  - ywhmyissuelogger
  - anotherissuelogger
  package: myissueloggerconfig
  path: ../../myissuelogger
- modules:
  - ywhmyissuelogger
  - anotherissuelogger
  package:
  path: ../../myissuelogger
```

A package is an item defining 3 elements:
- modules: list of module names
- package: name of the package, it can be empty if you just have python module-s.
- path: path to python package/module.

## Create Your Config Manager in Python

Our System detect all subclasses of ywh2bt.config.BugTrackerConfig abstract class, and append each of them as supported element in our global configuration manager.

A subclass of BugTrackerConfig, need to have a client class inherited from ywh2bt.trackers.bugtracker.BugTracker abstract class to work.
We show an example below.

According to the example above, to create the corresponding python code you have to create your package like this:
- `mkdir ../../myissuelogger`
- `> ../../myissuelogger/ywhmyissuelogger.py`
- `> ../../myissuelogger/anotherissuelogger.py`

NB: for module definition change
- `> ../../myissuelogger/ywhmyissuelogger.py`
- `> ../../myissuelogger/anotherissuelogger.py`
To :
- `mdir ../../myissuelogger/ywhmyissuelogger`
- `> ../../myissuelogger/ywhmyissuelogger/__init__.py`
- `mdir ../../myissuelogger/anotherissuelogger`
- `> ../../myissuelogger/anotherissuelogger/__init__.py`

Example of one possible body file ('../../myissuelogger/anotherissuelogger.py' for example).


```python
from client_package_sdk.client import ClientClass
from client_package_sdk.exceptions import ConnectError
from ywh2bt.trackers.bugtracker import BugTracker
from ywh2bt.config import BugTrackerConfig


class MyOwnClient(BugTracker):

    def __init__(self,
        url,
        login,
        project,
        token,
        assigned_to,
        issuetype="Task"
    ):
        self.url = url
        self.login = login
        self.project = project
        self.token = token
        self.assigned_to = assigned_to
        self.issuetype = issuetype
        try:
            self.bt = ClientClass(self.url, auth=(self.login, self.token))
        except ConnectError:
            raise

    def get_project(self):
        try:
            repo = self.bt.get_project(self.project)
        except HTTPError:
            raise
        return repo

    def post_issue(self, report):
        project = self.bt.projects.get(self.project)
        description = self.description_template
        for attachment in report.attachments:
            # Add attachment to gitlab issue if there is attachement in the original bug
            f = project.upload(attachment.original_name, attachment.data)
            description += "\n" + f["markdown"] + "\n"
        issue_data = {
            "title": self.issue_name_template.format(
                report_local_id=report.local_id, report_title=report.title
            ),
            "description": description.format(
                end_point=report.end_point,
                vulnerable_part=report.vulnerable_part,
                cvss=report.cvss.score,
                bug_type=report.bug_type.category.name,
                bug_description=report.bug_type.description,
                remediation_link=report.bug_type.link,
                description=report.description_html,
            ),
        }
        issue = project.issues.create(issue_data)
        return issue

    def get_url(self, issue):
        return issue.url

    def get_id(self, issue):
        return issue.id


class MyOwnConfig(BugTrackerConfig):

    bugtracker_type = "our_client"
    client = MyOwnClient
    mandatory_keys = ["url", "project", "assigned_to"]
    secret_keys = ["token"]
    optional_keys = dict(issuetype="Task")
    _description = dict(issuetype="valid issue name in MyOwnConfig system")

    def _set_bugtracker(self):
        self._get_bugtracker(
            self._url,
            self._login
            self._project,
            self._token,
            self._assigned_to,
            issuetype=self._issuetype,
        )
```

A BugTracker client class need to implement 4 methods:
- ```def get_project(self):``` : return a project object
- ```def post_issue(self, report):```: post the issue according to the report on the client and return the issue
- ```def get_url(self, issue):```: return issue url
- ```def get_id(self, issue):```: return issue id


A BugTrackerConfig class nedd to have 2 class attributes:
- ```bugtracker_type```: name of the bugtracker for selection in configuration mode
- ```client```: client class

and optionnaly have 4 other:
- ```mandatory_keys```: List of str needed in configuration file
- ```secret_keys```: List of str, corresponding of all keys must be secret, but are clearly store in configure file in no interactive mode
- ```optional_keys```: dictionary wich each pairs of (key, value) correspond to (optional_key, default_value).
- ```_description```: dictionary which associate a description of an existing keys define un one of :
    - ```mandatory_keys```
    - ```secret_keys```
    - ```optional_keys```

And need one method :
- ```def _set_bugtracker(self)```: call to ```_get_bugtracker``` method of BugTrackerConfig with your client class ```__init__``` input.

NB: a ```project``` key must be present in ```mandatory_keys```, ```optional_keys``` or ```secret_keys```!

Each key in mandatory, optional or secret key is convert as protected attribute with get property access.



## Return code:

- 100 : YesWeHack Login error
- 110 : YesWeHack program access error
- 120 : Configuration error
- 130 : Configuration File not exist
- 200 : Login error on Bugtracker
- 210 : Project error on Bugtracker
- 220 : Configuration error on bugtracker
