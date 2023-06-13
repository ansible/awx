# controller_configuration.users

## Description

An Ansible Role to add users to on Ansible Controller.

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
|`controller_user_accounts`|`see below`|yes|Data structure describing your user entries described below.  Alias: users ||
|`controller_user_default_password`|""|no|Global variable to set the password for all users.||

### Enforcing defaults

The following Variables compliment each other.
If Both variables are not set, enforcing default values is not done.
Enabling these variables enforce default values on options that are optional in the controller API.
This should be enabled to enforce configuration and prevent configuration drift. It is recomended to be enabled, however it is not enforced by default.

Enabling this will enforce configurtion without specifying every option in the configuration files.

'controller_configuration_users_enforce_defaults' defaults to the value of 'controller_configuration_enforce_defaults' if it is not explicitly called. This allows for enforced defaults to be toggled for the entire suite of controller configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_users_enforce_defaults`|`False`|no|Whether or not to enforce default option values on only the applications role|
|`controller_configuration_enforce_defaults`|`False`|no|This variable enables enforced default values as well, but is shared across multiple roles, see above.|

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add user task does not include sensitive information.
`controller_configuration_user_secure_logging` defaults to the value of `controller_configuration_secure_logging` if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_user_secure_logging`|`False`|no|Whether or not to include the sensitive user role tasks in the log. Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

### Asynchronous Retry Variables

The following Variables set asynchronous retries for the role.
If neither of the retries or delay or retries are set, they will default to their respective defaults.
This allows for all items to be created, then checked that the task finishes successfully.
This also speeds up the overall role.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_async_retries`|30|no|This variable sets the number of retries to attempt for the role globally.|
|`controller_configuration_users_async_retries`|`{{ controller_configuration_async_retries }}`|no|This variable sets the number of retries to attempt for the role.|
|`controller_configuration_async_delay`|1|no|This sets the delay between retries for the role globally.|
|`controller_configuration_users_async_delay`|`controller_configuration_async_delay`|no|This sets the delay between retries for the role.|

## Data Structure

### User Account Variables

|Variable Name|Default Value|Required|Type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`username`|""|yes|str|The username of the user|
|`new_username`|""|yes|str|Setting this option will change the existing username (looked up via the username field).|
|`password`|"{{ controller_user_default_password }}"|no|str|The password of the user|
|`email`|""|yes|str|The email of the user|
|`first_name`|""|no|str|The first name of the user|
|`last_name`|""|no|str|The last name of the user|
|`is_superuser`|false|no|bool|Whether the user is a superuser|
|`is_system_auditor`|false|no|bool|Whether the user is an auditor|
|`organization`|""|no|str|The name of the organization the user belongs to.<br />Added in awx.awx >= 20.0.0 DOES NOT exist in ansible.controller yet.|
|`state`|`present`|no|str|Desired state of the resource.|
|`update_secrets`|true|no|bool| True will always change password if user specifies password, even if API gives $encrypted$ for password. False will only set the password if other values change too.|

### Standard user Data Structure

#### Json Example

```json
{
  "controller_user_accounts": [
    {
      "user": "jsmith",
      "is_superuser": false,
      "password": "p4ssword",
      "email": "jsmith@example.com"
    }
  ]
}
```

#### Yaml Example

```yaml
---
controller_user_accounts:
  - user: controller_user
    is_superuser: false
    password: controller_password
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
    - {role: infra.controller_configuration.users, when: controller_user_accounts is defined}
```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Tom Page](https://github.com/Tompage1994)
