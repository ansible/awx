# controller_configuration.ad_hoc_command

## Description

An Ansible Role to run a list of ad hoc commands on Ansible Controller.

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
|`controller_oauthtoken`|""|no|Controller Admin User's token on the Ansible Controller Server. This should be stored in an Ansible Vault at or elsewhere and called from a parent playbook. Either username / password or oauthtoken need to be specified.||
|`controller_ad_hoc_commands`|`see below`|yes|Data structure describing your ad hoc commands to run Described below.||

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add ad hoc commands task does not include sensitive information.
controller_configuration_ad_hoc_command_secure_logging defaults to the value of controller_configuration_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of controller configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_ad_hoc_command_secure_logging`|`False`|no|Whether or not to include the sensitive ad_hoc_command role tasks in the log. Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

## Data Structure

### Ad Hoc Command Variables

|Variable Name|Default Value|Required|Type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`job_type`|"run"|no|str|Job_type to use for the ad hoc command. Either run or check.|
|`inventory`|""|yes|str|Inventory to use for the ad hoc command.|
|`limit`|`False`|no|str|Limit to use for the ad hoc command.|
|`credential`|""|yes|str|Credential to use for ad hoc command.|
|`execution_environment`|""|no|str|Execution Environment to use for ad hoc command.|
|`module_name`|""|str|yes|The Ansible module to execute.|
|`module_args`|`False`|no|str|The arguments to pass to the module.|
|`forks`|0|yes|int|The number of forks to use for this ad hoc execution.|
|`verbosity`|0|no|int|Verbosity level for this ad hoc command run|
|`extra_vars`|`False`|no|dict|Extra variables to use for the ad hoc command.|
|`become_enabled`|""|no|bool|If the become flag should be set.|
|`diff_mode`|""|no|bool|Show the changes made by Ansible tasks where supported|
|`wait`|`False`|no|bool|Wait for the command to complete.|
|`interval`|2|no|int|The interval to request an update from controller.|
|`timeout`|""|no|int|If waiting for the command to complete this will abort after this amount of seconds.|

### Standard Project Data Structure

#### Yaml Example

```yaml
---
controller_ad_hoc_commands:
  - job_type: run
    inventory: localhost
    credential: Demo Credential
    module_name: ping


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
    - {role: awx.controller_configuration.ad_hoc_command, when: controller_ad_hoc_commands is defined}

```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Sean Sullivan](https://github.com/sean-m-sullivan)
