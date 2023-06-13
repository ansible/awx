# controller_configuration.inventories

## Description

An Ansible Role to create inventories on Ansible Controller.

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
|`controller_inventories`|`see below`|yes|Data structure describing your inventories described below. Alias: inventory ||

### Enforcing defaults

The following Variables compliment each other.
If Both variables are not set, enforcing default values is not done.
Enabling these variables enforce default values on options that are optional in the controller API.
This should be enabled to enforce configuration and prevent configuration drift. It is recomended to be enabled, however it is not enforced by default.

Enabling this will enforce configurtion without specifying every option in the configuration files.

'controller_configuration_inventories_enforce_defaults' defaults to the value of 'controller_configuration_enforce_defaults' if it is not explicitly called. This allows for enforced defaults to be toggled for the entire suite of controller configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_inventories_enforce_defaults`|`False`|no|Whether or not to enforce default option values on only the applications role|
|`controller_configuration_enforce_defaults`|`False`|no|This variable enables enforced default values as well, but is shared across multiple roles, see above.|

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add inventories task does not include sensitive information.
controller_configuration_inventories_secure_logging defaults to the value of controller_configuration_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_inventories_secure_logging`|`False`|no|Whether or not to include the sensitive Inventory role tasks in the log. Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

### Asynchronous Retry Variables

The following Variables set asynchronous retries for the role.
If neither of the retries or delay or retries are set, they will default to their respective defaults.
This allows for all items to be created, then checked that the task finishes successfully.
This also speeds up the overall role.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_async_retries`|30|no|This variable sets the number of retries to attempt for the role globally.|
|`controller_configuration_inventories_async_retries`|`{{ controller_configuration_async_retries }}`|no|This variable sets the number of retries to attempt for the role.|
|`controller_configuration_async_delay`|1|no|This sets the delay between retries for the role globally.|
|`controller_configuration_inventories_async_delay`|`controller_configuration_async_delay`|no|This sets the delay between retries for the role.|

### Formating Variables

Variables can use a standard Jinja templating format to describe the resource.

Example:

```json
{{ variable }}
```

Because of this it is difficult to provide controller with the required format for these fields.

The workaround is to use the following format:

```json
{  { variable }}
```

The role will strip the double space between the curly bracket in order to provide controller with the correct format for the Variables.

## Data Structure

### Inventory Variables

|Variable Name|Default Value|Required|type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`name`|""|yes|str|Name of this inventory.|
|`new_name`|""|no|Setting this option will change the existing name (looked up via the name field).|
|`copy_from`|""|no|str|Name or id to copy the inventory from. This will copy an existing inventory and change any parameters supplied.|
|`description`|""|no|str|Description of this inventory.|
|`organization`|""|yes|str|Organization this inventory belongs to.|
|`instance_groups`|""|no|list|List of Instance Groups for this Inventory to run on.|
|`input_inventories`|""|no|list|List of Inventories to use as input for Constructed Inventory.|
|`variables`|`{}`|no|dict|Variables for the inventory.|
|`kind`|""|no|str|The kind of inventory. Currently choices are '' and 'smart'|
|`host_filter`|""|no|str|The host filter field, useful only when 'kind=smart'|
|`prevent_instance_group_fallback`|`False`|no|bool|Prevent falling back to instance groups set on the organization|
|`state`|`present`|no|str|Desired state of the resource.|

### Standard Inventory Data Structure

#### Json Example

```json
{
  "controller_inventories": [
    {
      "name": "RHVM-01",
      "organization": "Satellite",
      "description": "created by Ansible Playbook - for RHVM-01"
    },
    {
      "name": "Test Inventory - Smart",
      "organization": "Default",
      "description": "created by Ansible Playbook",
      "kind": "smart",
      "host_filter": "name__icontains=localhost"
    }
  ]
}

```

#### Yaml Example

```yaml
---
controller_inventories:
  - name: RHVM-01
    organization: Satellite
    description: created by Ansible Playbook - for RHVM-01
  - name: Test Inventory - Smart
    organization: Default
    description: created by Ansible Playbook
    kind: smart
    host_filter:  "name__icontains=localhost"

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
    - {role: awx.controller_configuration.inventories, when: controller_inventories is defined}
```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Edward Quail](mailto:equail@redhat.com)

[Andrew J. Huffman](https://github.com/ahuffman)

[Kedar Kulkarni](https://github.com/kedark3)
