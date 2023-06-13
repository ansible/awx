# controller_configuration.roles

## Description

An Ansible Role to create RBAC Entries on Ansible Controller.

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
|`controller_roles`|`see below`|yes|Data structure describing your RBAC entries described below.||

### Enforcing defaults

The following Variables compliment each other.
If Both variables are not set, enforcing default values is not done.
Enabling these variables enforce default values on options that are optional in the controller API.
This should be enabled to enforce configuration and prevent configuration drift. It is recomended to be enabled, however it is not enforced by default.

Enabling this will enforce configurtion without specifying every option in the configuration files.

'controller_configuration_role_enforce_defaults' defaults to the value of 'controller_configuration_enforce_defaults' if it is not explicitly called. This allows for enforced defaults to be toggled for the entire suite of controller configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_role_enforce_defaults`|`False`|no|Whether or not to enforce default option values on only the applications role|
|`controller_configuration_enforce_defaults`|`False`|no|This variable enables enforced default values as well, but is shared across multiple roles, see above.|

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add rbac task does not include sensitive information.
`controller_configuration_role_secure_logging` defaults to the value of `controller_configuration_secure_logging` if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_role_secure_logging`|`False`|no|Whether or not to include the sensitive rbac role tasks in the log.  Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

### Asynchronous Retry Variables

The following Variables set asynchronous retries for the role.
If neither of the retries or delay or retries are set, they will default to their respective defaults.
This allows for all items to be created, then checked that the task finishes successfully.
This also speeds up the overall role.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_async_retries`|30|no|This variable sets the number of retries to attempt for the role globally.|
|`controller_configuration_role_async_retries`|`{{ controller_configuration_async_retries }}`|no|This variable sets the number of retries to attempt for the role.|
|`controller_configuration_async_delay`|1|no|This sets the delay between retries for the role globally.|
|`controller_configuration_role_async_delay`|`controller_configuration_async_delay`|no|This sets the delay between retries for the role.|

## Data Structure

### Role Variables

|Variable Name|Default Value|Required|Type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`user`|""|no|str|The user for which the role applies|
|`users`|""|no|list|The users for which the role applies|
|`team`|""|no|str|The team for which the role applies|
|`teams`|""|no|list|The teams for which the role applies|
|`role`|""|no|str (see note below)|The role which is applied to one of {`target_team`, `inventory`, `job_template`, `target_team`, `inventory`, `job_template`} for either `user` or `team` |
|`target_team`|""|no|str|The team the role applies against|
|`target_teams`|""|no|list|The teams the role applies against|
|`inventory`|""|no|str|The inventory the role applies against|
|`inventories`|""|no|list|The inventories the role applies against|
|`job_template`|""|no|str|The job template the role applies against|
|`job_templates`|""|no|list|The job templates the role applies against|
|`workflow`|""|no|str|The workflow the role applies against|
|`workflows`|""|no|list|The workflows the role applies against|
|`credential`|""|no|str|The credential the role applies against|
|`credentials`|""|no|list|The credentials the role applies against|
|`organization`|""|no|str|The organization the role applies against|
|`organizations`|""|no|list|The organizations the role applies against|
|`lookup_organization`|""|no|str|Organization the inventories, job templates, projects, or workflows the items exists in. Used to help lookup the object, for organization roles see organization. If not provided, will lookup by name only, which does not work with duplicates.|
|`project`|""|no|str|The project the role applies against|
|`projects`|""|no|list|The project the role applies against|
|`state`|`present`|no|str|Desired state of the resource.|

#### Role

`role` must be one of the following:

- `admin`
- `read`
- `member`
- `execute`
- `adhoc`
- `update`
- `use`
- `auditor`
- `project_admin`
- `inventory_admin`
- `credential_admin`
- `workflow_admin`
- `notification_admin`
- `job_template_admin`

### Standard RBAC Data Structure

#### Json Example

```json
{
  "controller_roles": [
    {
      "user": "jdoe",
      "target_team": "My Team",
      "role": "member"
    },
    {
      "team": "My Team",
      "organization": "Default",
      "role": "execute"
    }
  ]
}
```

#### Yaml Example

```yaml
---
controller_roles:
- user: jdoe
  users:
    - thing1
    - thing2
  target_team: "My Team"
  role: member
- team: "My Team"
  organization: "Default"
  role: execute
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
    - {role: awx.controller_configuration.roles, when: controller_roles is defined}
```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Tom Page](https://github.com/Tompage1994)
