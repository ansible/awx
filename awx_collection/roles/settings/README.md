# controller_configuration.settings

An Ansible role to alter Settings on Ansible Controller.

## Requirements

ansible-galaxy collection install awx.awx

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
|`controller_settings`|`see below`|yes|Data structure describing your settings described below.||

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add settings task does not include sensitive information.
controller_configuration_settings_secure_logging defaults to the value of controller_configuration_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_settings_secure_logging`|`False`|no|Whether or not to include the sensitive Settings role tasks in the log. Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

### Asynchronous Retry Variables

The following Variables set asynchronous retries for the role.
If neither of the retries or delay or retries are set, they will default to their respective defaults.
This allows for all items to be created, then checked that the task finishes successfully.
This also speeds up the overall role.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_async_retries`|30|no|This variable sets the number of retries to attempt for the role globally.|
|`controller_configuration_settings_async_retries`|`{{ controller_configuration_async_retries }}`|no|This variable sets the number of retries to attempt for the role.|
|`controller_configuration_async_delay`|1|no|This sets the delay between retries for the role globally.|
|`controller_configuration_settings_async_delay`|`controller_configuration_async_delay`|no|This sets the delay between retries for the role.|

## Data Structure

There are two choices for entering settings. Either provide as a single dict under `settings` or individually as `name` `value`. In the first case `controller_settings` will simply be an individual dict, but in the second case, it will be a list.

### Setting Variables

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`settings`|{}|no|Dict of key-value pairs of settings|
|`name`|""|no|Name of the setting to set.|
|`value`|""|no|Value of the setting.|

### Standard Setting Data Structure - as a dict

#### Json Dict Example

```json
{
  "controller_settings": {
    "settings": {
      "AUTH_LDAP_USER_DN_TEMPLATE": "uid=%(user)s,ou=Users,dc=example,dc=com",
      "AUTH_LDAP_BIND_PASSWORD": "password"
    }
  }
}

```

#### Yaml Dict Example

```yaml
---
controller_settings:
  settings:
    AUTH_LDAP_USER_DN_TEMPLATE: "uid=%(user)s,ou=Users,dc=example,dc=com"
    AUTH_LDAP_BIND_PASSWORD: "password"

```

### Standard Setting Data Structure - as a list

#### Json List Example

```json
{
  "controller_settings": [
    {
      "name": "AUTH_LDAP_USER_DN_TEMPLATE",
      "value": "uid=%(user)s,ou=Users,dc=example,dc=com"
    },
    {
      "name": "AUTH_LDAP_BIND_PASSWORD",
      "value": "password"
    }
  ]
}

```

#### Yaml List Example

```yaml
---
controller_settings:
  - name: AUTH_LDAP_USER_DN_TEMPLATE
    value: "uid=%(user)s,ou=Users,dc=example,dc=com"
  - name: AUTH_LDAP_BIND_PASSWORD
    value: "password"
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
    - {role: awx.controller_configuration.settings, when: controller_settings is defined}
```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Kedar Kulkarni](https://github.com/kedark3)
[Sean Sullivan](https://github.com/sean-m-sullivan)
