# controller_configuration.organizations

## Description

An Ansible Role to create Organizations on Ansible Controller.

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
|`controller_state`|"present"|no|The state all objects will take unless overridden by object default|'absent'|
|`controller_hostname`|""|yes|URL to the Ansible Controller Server.|127.0.0.1|
|`controller_validate_certs`|`True`|no|Whether or not to validate the Ansible Controller Server's SSL certificate.||
|`controller_username`|""|no|Admin User on the Ansible Controller Server. Either username / password or oauthtoken need to be specified.||
|`controller_password`|""|no|Controller Admin User's password on the Ansible Controller Server. This should be stored in an Ansible Vault at vars/controller-secrets.yml or elsewhere and called from a parent playbook. Either username / password or oauthtoken need to be specified.||
|`controller_oauthtoken`|""|no|Controller Admin User's token on the Ansible Controller Server. This should be stored in an Ansible Vault at or elsewhere and called from a parent playbook. Either username / password or oauthtoken need to be specified.|||
|`controller_organizations`|`see below`|yes|Data structure describing your organization or organizations Described below. Alias: organizations ||

### Enforcing defaults

The following Variables compliment each other.
If Both variables are not set, enforcing default values is not done.
Enabling these variables enforce default values on options that are optional in the controller API.
This should be enabled to enforce configuration and prevent configuration drift. It is recomended to be enabled, however it is not enforced by default.

Enabling this will enforce configurtion without specifying every option in the configuration files.

'controller_configuration_organizations_enforce_defaults' defaults to the value of 'controller_configuration_enforce_defaults' if it is not explicitly called. This allows for enforced defaults to be toggled for the entire suite of controller configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_organizations_enforce_defaults`|`False`|no|Whether or not to enforce default option values on only the applications role|
|`controller_configuration_enforce_defaults`|`False`|no|This variable enables enforced default values as well, but is shared across multiple roles, see above.|

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add organization task does not include sensitive information.
controller_configuration_organizations_secure_logging defaults to the value of controller_configuration_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_organizations_secure_logging`|`False`|no|Whether or not to include the sensitive Organization role tasks in the log. Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

### Asynchronous Retry Variables

The following Variables set asynchronous retries for the role.
If neither of the retries or delay or retries are set, they will default to their respective defaults.
This allows for all items to be created, then checked that the task finishes successfully.
This also speeds up the overall role.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_async_retries`|30|no|This variable sets the number of retries to attempt for the role globally.|
|`controller_configuration_organizations_async_retries`|`{{ controller_configuration_async_retries }}`|no|This variable sets the number of retries to attempt for the role.|
|`controller_configuration_async_delay`|1|no|This sets the delay between retries for the role globally.|
|`controller_configuration_organizations_async_delay`|`controller_configuration_async_delay`|no|This sets the delay between retries for the role.|

## Organization Data Structure

This role accepts two data models. A simple straightforward easy to maintain model, and another based on the controller api. The 2nd one is more complicated and includes more detail, and is compatible with controller import/export.

### Organization Variables

|Variable Name|Default Value|Required|Type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`name`|""|yes|str|Name of Organization|
|`description`|`False`|no|str|Description of  of Organization.|
|`custom_virtualenv`|""|no|str|Local absolute file path containing a custom Python virtualenv to use.|
|`max_hosts`|""|no|int|The max hosts allowed in this organization.|
|`instance_groups`|""|no|list|list of Instance Groups for this Organization to run on.|
|`galaxy_credentials`|""|no|list|The credentials to use with private automationhub.|
|`default_environment`|""|no|str|Default Execution Environment to use for jobs owned by the Organization.|
|`notification_templates_started`|""|no|list|The notifications on started to use for this organization in a list.|
|`notification_templates_success`|""|no|list|The notifications on success to use for this organization in a list.|
|`notification_templates_error`|""|no|list|The notifications on error to use for this organization in a list.|
|`notification_templates_approvals`|""|no|list|The notifications for approval to use for this organization in a list.|
|`state`|`present`|no|str|Desired state of the resource.|
|`assign_galaxy_credentials_to_org`|`True`|no|bool|Boolean to indicate whether credentials should be assigned or not. It should be noted that credentials must exist before adding it. |
|`assign_default_ee_to_org`|`True`|no|bool|Boolean to indicate whether default execution environment should be assigned or not. It should be noted that execution environment must exist before adding it. |

### Standard Organization Data Structure model

#### Json Example

```json
{
    "controller_organizations": [
      {
        "name": "Default",
        "description": "This is the Default Group"
      },
      {
        "name": "Automation Group",
        "description": "This is the Automation Group",
        "custom_virtualenv": "/opt/cust/environment/",
        "max_hosts": 10,
        "galaxy_credentials": "Automation Hub",
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
controller_organizations:
- name: Default
  description: This is the Default Group
- name: Automation Group
  description: This is the Automation Group
  custom_virtualenv: "/opt/cust/environment/"
  max_hosts: 10
```

#### Controller Export Data structure model

##### Export Yaml Example

```yaml
---
controller_organizations:
- name: Satellite
  description: Satellite
  max_hosts: 0
  custom_virtualenv:
  related:
    notification_templates_started: []
    notification_templates_success: []
    notification_templates_error:
    - name: irc-satqe-chat-notification
    notification_templates_approvals: []
- name: Default
  description: Default
  max_hosts: 0
  custom_virtualenv:
  galaxy_credentials:
    - Automation Hub
  related:
    notification_templates_started: []
    notification_templates_success: []
    notification_templates_error: []
    notification_templates_approvals: []
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
    - {role: awx.controller_configuration.organizations, when: controller_organizations is defined}
```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Sean Sullivan](https://github.com/sean-m-sullivan)
