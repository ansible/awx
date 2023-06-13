# controller_configuration.project_update

## Description

An Ansible Role to update a list of projects on Ansible Controller.

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
|`controller_projects`|`see below`|yes|Data structure describing the project to update Described below. Alias: projects ||

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the project update task does not include sensitive information.
controller_configuration_project_update_secure_logging defaults to the value of controller_configuration_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_project_update_secure_logging`|`False`|no|Whether or not to include the sensitive Project role tasks in the log. Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

### Asynchronous Retry Variables

The following Variables set asynchronous retries for the role.
If neither of the retries or delay or retries are set, they will default to their respective defaults.
This allows for all items to be created, then checked that the task finishes successfully.
This also speeds up the overall role.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_async_retries`|60|no|This variable sets the number of retries to attempt for the role globally.|
|`controller_configuration_project_update_async_retries`|60|no|This variable sets the number of retries to attempt for the role.|
|`controller_configuration_async_delay`|10|no|This sets the delay between retries for the role globally.|
|`controller_configuration_project_update_async_delay`|10|no|This sets the delay between retries for the role.|

## Data Structure

### Project Update Variables

|Variable Name|Default Value|Required|Type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`name`|""|yes|str|The name or id of the project to update.|
|`organization`|""|no|str|Organization the project exists in. Used for lookup only.|
|`wait`|""|no|str|Wait for the project to complete.|
|`interval`|`controller_configuration_project_update_async_delay`|no|str|The interval to request an update from controller.|
|`timeout`|""|no|str|If waiting for the job to complete this will abort after this amount of seconds.|
|`update_project`|`False`|no|bool|If defined and true, the project update will be executed, otherwise it won't.|

### Standard Project Data Structure

#### Yaml Example

```yaml
---
controller_projects:
  - name: Test Project
    scm_type: git
    scm_url: https://github.com/ansible/tower-example.git
    scm_branch: master
    scm_clean: true
    description: Test Project 1
    organization: Satellite
    wait: true
  - name: Test Project 2
    scm_type: git
    scm_url: https://github.com/ansible/tower-example.git
    description: Test Project 2
    organization: Satellite
    wait: true
  - name: Test Inventory source project
    scm_type: git
    scm_url: https://github.com/ansible/ansible-examples.git
    description: ansible-examples
    organization: Satellite
    wait: true

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
    - {role: infra.controller_configuration.project_update, when: controller_projects is defined}

```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Sean Sullivan](https://github.com/sean-m-sullivan)
