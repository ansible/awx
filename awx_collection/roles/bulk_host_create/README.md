# controller_configuration.bulk_host_create

## Description

An Ansible Role to create bulk hosts on Ansible Controller.

## Requirements

ansible-galaxy collection install awx.awx

## Variables

### Authentication

|Variable Name|Default Value|Required|Description|Example|
|:---|:---:|:---:|:---|:---|
|`controller_hostname`|""|yes|URL to the Ansible Controller Server.|127.0.0.1|
|`controller_validate_certs`|`True`|no|Whether or not to validate the Ansible Controller Server's SSL certificate.||
|`controller_username`|""|no|Admin User on the Ansible Controller Server. Either username / password or oauthtoken need to be specified.||
|`controller_password`|""|no|Controller Admin User's password on the Ansible Controller Server. This should be stored in an Ansible Vault at vars/controller-secrets.yml or elsewhere and called from a parent playbook. Either username / password or oauthtoken need to be specified.||
|`controller_oauthtoken`|""|no|Controller Admin User's token on the Ansible Controller Server. This should be stored in an Ansible Vault at or elsewhere and called from a parent playbook. Either username / password or oauthtoken need to be specified.|||
|`controller_configuration_bulk_hosts_secure_logging`|`see below`|yes|Data structure describing your organization or organizations Described below.||

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add ******* task does not include sensitive information.
controller_configuration_*******_secure_logging defaults to the value of controller_configuration_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of controller configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_bulk_hosts_secure_logging`|`False`|no|Whether or not to include the sensitive ******* role tasks in the log. Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

### Asynchronous Retry Variables

The following Variables set asynchronous retries for the role.
If neither of the retries or delay or retries are set, they will default to their respective defaults.
This allows for all items to be created, then checked that the task finishes successfully.
This also speeds up the overall role.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_async_retries`|30|no|This variable sets the number of retries to attempt for the role globally.|
|`controller_configuration_bulk_hosts_async_retries`|`{{ controller_configuration_async_retries }}`|no|This variable sets the number of retries to attempt for the role.|
|`controller_configuration_async_delay`|1|no|This sets the delay between retries for the role globally.|
|`controller_configuration_bulk_hosts_async_delay`|`controller_configuration_async_delay`|no|This sets the delay between retries for the role.|

## Data Structure

### Bulk Host Variables

|Variable Name|Default Value|Required|Type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`hosts`|""|yes|list|List of hosts and host options to add to inventory. Documented below|
|`inventory`|""|yes|str|Inventory name or ID the hosts should be made a member of.|

### Bulk Host Sub Options

|Variable Name|Default Value|Required|Type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`name`|""|no|list|The name to use for the host.|
|`description`|""|no|str|The description to use for the host.|
|`enabled`|""|no|bool|If the host should be enabled.|
|`variables`|""|no|dict|Variables to use for the host.|
|`instance`|""|no|list|instance to use for the host.|

### Standard Project Data Structure

#### Json Example

```json
{
  "controller_bulk_hosts": [
    {
      "inventory": "localhost",
      "hosts": [
        {
          "name": "localhost"
        },
        {
          "name": "127.0.0.1",
          "variables": {
            "some_var": "some_val",
            "ansible_connection": "local"
          }
        }
      ]
    }
  ]
}
```

#### Yaml Example

```yaml
---
controller_bulk_hosts:
  - inventory: localhost
    hosts:
      - name: localhost
      - name: 127.0.0.1
        variables:
          some_var: some_val
          ansible_connection: local
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
    - {role: redhat_cop.controller_configuration.bulk_host_create, when: controller_bulk_hosts is defined}
```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Sean Sullivan](https://github.com/sean-m-sullivan)
