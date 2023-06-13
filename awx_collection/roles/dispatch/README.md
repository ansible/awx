# controller_configuration.dispatch

## Description

An Ansible Role to run all roles on Ansible Controller.

## Requirements

ansible-galaxy collection install -r tests/collections/requirements.yml to be installed
Currently:
  awx.awx
  or
  ansible.controller

## Variables

Each role has its own variables, for information on those please see each role which this role will call. This role has one key variable `controller_configuration_dispatcher_roles` and its default value is shown below:

```yaml
controller_configuration_dispatcher_roles:
  - {role: settings, var: controller_settings, tags: settings}
  - {role: organizations, var: controller_organizations, tags: organizations}
  - {role: labels, var: controller_labels, tags: labels}
  - {role: users, var: controller_user_accounts, tags: users}
  - {role: teams, var: controller_teams, tags: teams}
  - {role: credential_types, var: controller_credential_types, tags: credential_types}
  - {role: credentials, var: controller_credentials, tags: credentials}
  - {role: credential_input_sources, var: controller_credential_input_sources, tags: credential_input_sources}
  - {role: notification_templates, var: controller_notifications, tags: notification_templates}
  - {role: projects, var: controller_projects, tags: projects}
  - {role: execution_environments, var: controller_execution_environments, tags: execution_environments}
  - {role: applications, var: controller_applications, tags: applications}
  - {role: inventories, var: controller_inventories, tags: inventories}
  - {role: instance_groups, var: controller_instance_groups, tags: instance_groups}
  - {role: project_update, var: controller_projects, tags: projects}
  - {role: inventory_sources, var: controller_inventory_sources, tags: inventory_sources}
  - {role: inventory_source_update, var: controller_inventory_sources, tags: inventory_sources}
  - {role: hosts, var: controller_hosts, tags: hosts}
  - {role: groups, var: controller_groups, tags: inventories}
  - {role: job_templates, var: controller_templates, tags: job_templates}
  - {role: workflow_job_templates, var: controller_workflows, tags: workflow_job_templates}
  - {role: schedules, var: controller_schedules, tags: schedules}
  - {role: roles, var: controller_roles, tags: roles}
```

Note that each item has three elements:

- `role` which is the name of the role within infra.controller_configuration
- `var` which is the variable which is used in that role. We use this to prevent the role being called if the variable is not set
- `tags` the tags which are applied to the role so it is possible to apply tags to a playbook using the dispatcher with these tags.

It is possible to redefine this variable with a subset of roles or with different tags. In general we suggest keeping the same structure and perhaps just using a subset.

### Authentication

|Variable Name|Default Value|Required|Description|Example|
|:---|:---:|:---:|:---|:---|
|`controller_state`|"present"|no|The state all objects will take unless overridden by object default|'absent'|
|`controller_hostname`|""|yes|URL to the Ansible Controller Server.|127.0.0.1|
|`controller_validate_certs`|`True`|no|Whether or not to validate the Ansible Controller Server's SSL certificate.||
|`controller_username`|""|no|Admin User on the Ansible Controller Server. Either username / password or oauthtoken need to be specified.||
|`controller_password`|""|no|Controller Admin User's password on the Ansible Controller Server. This should be stored in an Ansible Vault at vars/controller-secrets.yml or elsewhere and called from a parent playbook. Either username / password or oauthtoken need to be specified.||
|`controller_oauthtoken`|""|no|Controller Admin User's token on the Ansible Controller Server. This should be stored in an Ansible Vault at or elsewhere and called from a parent playbook. Either username / password or oauthtoken need to be specified.||

### Secure Logging Variables

The role defaults to False as normally most projects task does not include sensitive information.
Each role the dispatch role calls has a separate variable which can be turned on to enforce secure logging for that role but defaults to the value of controller_configuration_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of configuration roles with a single variable, or for the user to selectively use it. If neither value is set then each role has a default value of true or false depending on the Red Hat COP suggestions.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_secure_logging`|""|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

### Asynchronous Retry Variables

The following Variables set asynchronous retries for the role.
If neither of the retries or delay or retries are set, they will default to their respective defaults.
This allows for all items to be created, then checked that the task finishes successfully.
This also speeds up the overall role. Each individual role has its own variable which can allow the individual setting of values. See each role for more the variable names.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_async_retries`|30|no|This variable sets the number of retries to attempt for the role globally.|
|`controller_configuration_async_delay`|1|no|This sets the delay between retries for the role globally.|

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
    - infra.controller_configuration.dispatch
```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Tom Page](https://github.com/Tompage1994)
