# controller_configuration.projects

## Description

An Ansible Role to create Projects on Ansible Controller.

## Requirements

ansible-galaxy collection install -r tests/collections/requirements.yml to be installed
Currently:
  awx.awx
  or
  ansible.controller

## Variables

### Authentication

|Variable Name|Default Value|Required|Description|Example|
|:---|:---:|:---:|:---|:---|
|`controller_state`|"present"|no|str|The state all objects will take unless overridden by object default|'absent'|
|`controller_hostname`|""|yes|str|URL to the Ansible Controller Server.|127.0.0.1|
|`controller_validate_certs`|`True`|no|str|Whether or not to validate the Ansible Controller Server's SSL certificate.||
|`controller_username`|""|no|str|Admin User on the Ansible Controller Server. Either username / password or oauthtoken need to be specified.||
|`controller_password`|""|no|str|Controller Admin User's password on the Ansible Controller Server. This should be stored in an Ansible Vault at vars/controller-secrets.yml or elsewhere and called from a parent playbook. Either username / password or oauthtoken need to be specified.||
|`controller_oauthtoken`|""|no|str|Controller Admin User's token on the Ansible Controller Server. This should be stored in an Ansible Vault at or elsewhere and called from a parent playbook. Either username / password or oauthtoken need to be specified.|||
|`controller_projects`|`see below`|yes|str|Data structure describing your project or projects Described below. Alias: projects ||

### Enforcing defaults

The following Variables compliment each other.
If Both variables are not set, enforcing default values is not done.
Enabling these variables enforce default values on options that are optional in the controller API.
This should be enabled to enforce configuration and prevent configuration drift. It is recomended to be enabled, however it is not enforced by default.

Enabling this will enforce configurtion without specifying every option in the configuration files.

'controller_configuration_projects_enforce_defaults' defaults to the value of 'controller_configuration_enforce_defaults' if it is not explicitly called. This allows for enforced defaults to be toggled for the entire suite of controller configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_projects_enforce_defaults`|`False`|no|Whether or not to enforce default option values on only the applications role|
|`controller_configuration_enforce_defaults`|`False`|no|This variable enables enforced default values as well, but is shared across multiple roles, see above.|

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add projects task does not include sensitive information.
controller_configuration_projects_secure_logging defaults to the value of controller_configuration_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_projects_secure_logging`|`False`|no|str|Whether or not to include the sensitive Project role tasks in the log. Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|str|This variable enables secure logging as well, but is shared across multiple roles, see above.|

### Asynchronous Retry Variables

The following Variables set asynchronous retries for the role.
If neither of the retries or delay or retries are set, they will default to their respective defaults.
This allows for all items to be created, then checked that the task finishes successfully.
This also speeds up the overall role.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_async_retries`|30|no|str|This variable sets the number of retries to attempt for the role globally.|
|`controller_configuration_projects_async_retries`|`{{ controller_configuration_async_retries }}`|no|str|This variable sets the number of retries to attempt for the role.|
|`controller_configuration_async_delay`|1|no|str|This sets the delay between retries for the role globally.|
|`controller_configuration_projects_async_delay`|`controller_configuration_async_delay`|no|str|This sets the delay between retries for the role.|

## Data Structure

### Project Variables

|Variable Name|Default Value|Required|Type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`name`|""|yes|str|Name of Project|
|`new_name`|""|no|Setting this option will change the existing name (looked up via the name field).|
|`copy_from`|""|no|str|Name or id to copy the project from. This will copy an existing project and change any parameters supplied.|
|`description`|`False`|no|str|Description of the Project.|
|`organization`|`False`|yes|str|Name of organization for project.|
|`scm_type`|""|no|str|Type of SCM resource.|
|`scm_url`|""|no|str|URL of SCM resource.|
|`default_environment`|""|no|str|Default Execution Environment to use for jobs relating to the project.|
|`local_path`|""|no|str|The server playbook directory for manual projects.|
|`scm_branch`|""|no|str|The branch to use for the SCM resource.|
|`scm_refspec`|""|no|str|The refspec to use for the SCM resource.|
|`credential`|""|no|str|Name of the credential to use with this SCM resource.|
|`signature_validation_credential`|""|no|str|Name of the credential to use for signature validation. If signature validation credential is provided, signature validation will be enabled.|
|`scm_clean`|""|no|bool|Remove local modifications before updating.|
|`scm_delete_on_update`|""|no|bool|Remove the repository completely before updating.|
|`scm_track_submodules`|""|no|bool|Track submodules latest commit on specified branch.|
|`scm_update_on_launch`|""|no|bool|Before an update to the local repository before launching a job with this project.|
|`scm_update_cache_timeout`|""|no|str|Cache Timeout to cache prior project syncs for a certain number of seconds. Only valid if scm_update_on_launch is to True, otherwise ignored.|
|`allow_override`|""|no|str|Allow changing the SCM branch or revision in a job template that uses this project.|
|`timeout`|""|no|int|The amount of time (in seconds) to run before the SCM Update is canceled. A value of 0 means no timeout.|
|`custom_virtualenv`|""|no|str|Local absolute file path containing a custom Python virtualenv to use.|
|`notification_templates_started`|""|no|list|The notifications on started to use for this organization in a list.|
|`notification_templates_success`|""|no|list|The notifications on success to use for this organization in a list.|
|`notification_templates_error`|""|no|list|The notifications on error to use for this organization in a list.|
|`state`|`present`|no|str|Desired state of the resource.|
|`wait`|""|no|bool|Provides option to wait for completed project sync before returning.|
|`update_project`|`False`|no|bool|Force project to update after changes.Used in conjunction with wait, interval, and timeout.|
|`interval`|`controller_configuration_projects_async_delay`|no|float|The interval to request an update from controller. Requires wait.|

### Standard Project Data Structure

#### Json Example

```json
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
      ansible.builtin.include_vars:
        dir: ./yaml
        ignore_files: [controller_config.yml.template]
        extensions: ["yml"]
  roles:
    - {role: infra.controller_configuration.projects, when: controller_projects is defined}
```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Sean Sullivan](https://github.com/sean-m-sullivan)
