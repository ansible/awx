# controller_configuration.projects
## Description
An Ansible Role to create Projects on Ansible Controller.

## Requirements
ansible-galaxy collection install  -r tests/collections/requirements.yml to be installed
Currently:
  awx.awx
  or
  ansible.controller

## Variables

### Authentication
|Variable Name|Default Value|Required|Description|Example|
|:---:|:---:|:---:|:---:|:---:|
|`controller_state`|"present"|no|The state all objects will take unless overriden by object default|'absent'|
|`controller_check_mode`|"present"|no|The check_mode of all objects will take unless overriden by object default|'absent'|
|`controller_ignore_errors`|"present"|no|The ignore_errors state of all objects will take unless overriden by object default|'absent'|
|`controller_hostname`|""|yes|URL to the Ansible Controller Server.|127.0.0.1|
|`controller_validate_certs`|`True`|no|Whether or not to validate the Ansible Controller Server's SSL certificate.||
|`controller_username`|""|yes|Admin User on the Ansible Controller Server.||
|`controller_password`|""|yes|Controller Admin User's password on the Ansible Controller Server.  This should be stored in an Ansible Vault at vars/controller-secrets.yml or elsewhere and called from a parent playbook.||
|`controller_oauthtoken`|""|yes|Controller Admin User's token on the Ansible Controller Server.  This should be stored in an Ansible Vault at or elsewhere and called from a parent playbook.||
|`controller_projects`|`see below`|yes|Data structure describing your project or projects Described below.||

### Secure Logging Variables
The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add projects task does not include sensitive information.
controller_configuration_projects_secure_logging defaults to the value of controller_configuration_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_projects_secure_logging`|`False`|no|Whether or not to include the sensitive Project role tasks in the log.  Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared accross multiple roles, see above.|

## Data Structure
### Variables
|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`name`|""|yes|Name of Project|
|`copy_from`|""|no|Name or id to copy the proejct from. This will copy an existing project and change any parameters supplied.|
|`description`|`False`|no|Description of the Project.|
|`organization`|`False`|yes|Name of organization for project.|
|`scm_type`|""|no|Type of SCM resource.|
|`scm_url`|""|no|URL of SCM resource.|
|`default_environment`|""|no|Default Execution Environment to use for jobs relating to the project.|
|`local_path`|""|no|The server playbook directory for manual projects.|
|`scm_branch`|""|no|The branch to use for the SCM resource.|
|`scm_refspec`|""|no|The refspec to use for the SCM resource.|
|`credential`|""|no|Name of the credential to use with this SCM resource.|
|`scm_clean`|""|no|Remove local modifications before updating.|
|`scm_delete_on_update`|""|no|Remove the repository completely before updating.|
|`scm_track_submodules`|""|no|Track submodules latest commit on specified branch.|
|`scm_update_on_launch`|""|no|Before an update to the local repository before launching a job with this project.|
|`scm_update_cache_timeout`|""|no|Cache Timeout to cache prior project syncs for a certain number of seconds. Only valid if scm_update_on_launch is to True, otherwise ignored.|
|`allow_override`|""|no|Allow changing the SCM branch or revision in a job template that uses this project.|
|`timeout`|""|no|The amount of time (in seconds) to run before the SCM Update is canceled. A value of 0 means no timeout.|
|`custom_virtualenv`|""|no|Local absolute file path containing a custom Python virtualenv to use.|
|`notification_templates_started`|""|no|The notifications on started to use for this organization in a list.|
|`notification_templates_success`|""|no|The notifications on success to use for this organization in a list.|
|`notification_templates_error`|""|no|The notifications on error to use for this organization in a list.|
|`state`|`present`|no|Desired state of the resource.|
|`wait`|""|no|Provides option to wait for completed project sync before returning.|
|`update_project`|""|no|Force project to update after changes.Used in conjunction with wait, interval, and timeout.|
|`interval`|1|no|The interval to request an update from controller. Requires wait.|
|`check_mode`||no|Desired check mode of the resource.|
|`ignore_errors`||no|Desired ignore errors of the resource.|
### Standard Project Data Structure
#### Json Example
```json
---
{
    "controller_projects": [
      {
        "name": "controller Config",
        "organization": "Default",
        "scm_branch": "master",
        "scm_clean": "no",
        "scm_delete_on_update": "no",
        "scm_type": "git",
        "scm_update_on_launch": "no",
        "scm_url": "https://github.com/ansible/tower-example.git",
        "notification_templates_error": [
          "Slack_for_testing"
        ]
      }
    ]
  }

```
#### Yaml Example
```yaml
---
controller_projects:
- name: controller Config
  organization: Default
  scm_branch: master
  scm_clean: 'no'
  scm_delete_on_update: 'no'
  scm_type: git
  scm_update_on_launch: 'no'
  scm_url: https://github.com/ansible/tower-example.git
  notification_templates_error:
  - Slack_for_testing

```
## Playbook Examples
### Standard Role Usage
```yaml
---
- name: Playbook to configure ansible controller post installation
  hosts: localhost
  connection: local
  # Define following vars here, or in controller_configs/controller_auth.yml
  # controller_hostname: ansible-controller-web-svc-test-project.example.com
  # controller_username: admin
  # controller_password: changeme
  pre_tasks:
    - name: Include vars from controller_configs directory
      include_vars:
        dir: ./yaml
        ignore_files: [controller_config.yml.template]
        extensions: ["yml"]
  roles:
    - {role: awx.awx.projects, when: controller_projects is defined}
```
## License
[MIT](LICENSE)

## Author
[Sean Sullivan](https://github.com/sean-m-sullivan)
