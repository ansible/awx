# controller_configuration.inventory_sources

## Description

An Ansible role to create inventory sources on Ansible Controller.

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
|`controller_inventory_sources`|`see below`|yes|Data structure describing your inventory sources Described below. Alias: inventory_sources ||

### Enforcing defaults

The following Variables compliment each other.
If Both variables are not set, enforcing default values is not done.
Enabling these variables enforce default values on options that are optional in the controller API.
This should be enabled to enforce configuration and prevent configuration drift. It is recomended to be enabled, however it is not enforced by default.

Enabling this will enforce configurtion without specifying every option in the configuration files.

'controller_configuration_inventory_sources_enforce_defaults' defaults to the value of 'controller_configuration_enforce_defaults' if it is not explicitly called. This allows for enforced defaults to be toggled for the entire suite of controller configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_inventory_sources_enforce_defaults`|`False`|no|Whether or not to enforce default option values on only the applications role|
|`controller_configuration_enforce_defaults`|`False`|no|This variable enables enforced default values as well, but is shared across multiple roles, see above.|

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add inventory_source task does not include sensitive information.
controller_configuration_inventory_sources_secure_logging defaults to the value of controller_configuration_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_inventory_sources_secure_logging`|`False`|no|Whether or not to include the sensitive Inventory Sources role tasks in the log. Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

### Asynchronous Retry Variables

The following Variables set asynchronous retries for the role.
If neither of the retries or delay or retries are set, they will default to their respective defaults.
This allows for all items to be created, then checked that the task finishes successfully.
This also speeds up the overall role.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_async_retries`|30|no|This variable sets the number of retries to attempt for the role globally.|
|`controller_configuration_inventory_sources_async_retries`|`{{ controller_configuration_async_retries }}`|no|This variable sets the number of retries to attempt for the role.|
|`controller_configuration_async_delay`|1|no|This sets the delay between retries for the role globally.|
|`controller_configuration_inventory_sources_async_delay`|`controller_configuration_async_delay`|no|This sets the delay between retries for the role.|

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

### Inventory Sources Variables

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`name`|""|yes|The name to use for the inventory source.|
|`new_name`|""|no|A new name for this assets (will rename the asset).|
|`description`|`False`|no|The description to use for the inventory source.|
|`inventory`|""|yes|Inventory the group should be made a member of.|
|`organization`|""|no|Organization the inventory belongs to.|
|`source`|""|no|The source to use for this group.|
|`source_path`|""|no|For an SCM based inventory source, the source path points to the file within the repo to use as an inventory.|
|`source_vars`|""|no|The variables or environment fields to apply to this source type.|
|`enabled_var`|""|no|The variable to use to determine enabled state e.g., "status.power_state".|
|`enabled_value`|""|no|Value when the host is considered enabled, e.g., "powered_on".|
|`host_filter`|""|no|If specified, controller will only import hosts that match this regular expression.|
|`limit`|""|no|Enter host, group or pattern match.|
|`credential`|""|no|Credential to use for the source.|
|`execution_environment`|""|no|Execution Environment to use for the source.|
|`overwrite`|""|no|Delete child groups and hosts not found in source.|
|`overwrite_vars`|""|no|Override vars in child groups and hosts with those from external source.|
|`custom_virtualenv`|""|no|Local absolute file path containing a custom Python virtualenv to use.|
|`timeout`|""|no|The amount of time (in seconds) to run before the task is canceled.|
|`verbosity`|""|no|The verbosity level to run this inventory source under.|
|`update_on_launch`|""|no|Refresh inventory data from its source each time a job is run.|
|`update_cache_timeout`|""|no|Time in seconds to consider an inventory sync to be current.|
|`source_project`|""|no|Project to use as source with scm option.|
|`scm_branch`|""|no|Project scm branch to use as source with scm option. Project must have branch override enabled.|
|`state`|`present`|no|Desired state of the resource.|
|`notification_templates_started`|""|no|The notifications on started to use for this inventory source in a list.|
|`notification_templates_success`|""|no|The notifications on success to use for this inventory source in a list.|
|`notification_templates_error`|""|no|The notifications on error to use for this inventory source in a list.|

### Standard Inventory Source Data Structure

#### Json Example

```json
{
  "controller_inventory_sources": [
    {
      "name": "RHVM-01",
      "source": "rhv",
      "inventory": "RHVM-01",
      "credential": "admin@internal-RHVM-01",
      "description": "created by Ansible controller",
      "overwrite": true,
      "update_on_launch": true,
      "update_cache_timeout": 0
    }
  ]
}

```

#### Yaml Example

```yaml
---
controller_inventory_sources:
  - name: RHVM-01
    source: rhv
    inventory: RHVM-01
    credential: admin@internal-RHVM-01
    description: created by Ansible controller
    overwrite: true
    update_on_launch: true
    update_cache_timeout: 0

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
    - {role: awx.controller_configuration.inventory_sources, when: controller_inventory_sources is defined}
```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Edward Quail](mailto:equail@redhat.com)

[Andrew J. Huffman](https://github.com/ahuffman)

[Kedar Kulkarni](https://github.com/kedark3)
