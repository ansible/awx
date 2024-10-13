# controller_configuration.bulk_job_launch

## Description

An Ansible Role to launch bulk jobs on Ansible Controller.

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
|`controller_bulk_launch_jobs`|`see below`|yes|Data structure describing your organization or organizations Described below.||

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add ******* task does not include sensitive information.
controller_configuration_*******_secure_logging defaults to the value of controller_configuration_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of controller configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_bulk_job_launch_secure_logging`|`False`|no|Whether or not to include the sensitive bulk_job_launch role tasks in the log. Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

### Asynchronous Retry Variables

The following Variables set asynchronous retries for the role.
If neither of the retries or delay or retries are set, they will default to their respective defaults.
This allows for all items to be created, then checked that the task finishes successfully.
This also speeds up the overall role.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_async_retries`|30|no|This variable sets the number of retries to attempt for the role globally.|
|`controller_configuration_bulk_job_launch_async_retries`|`{{ controller_configuration_async_retries }}`|no|This variable sets the number of retries to attempt for the role.|
|`controller_configuration_async_delay`|1|no|This sets the delay between retries for the role globally.|
|`controller_configuration_bulk_job_launch_async_delay`|`controller_configuration_async_delay`|no|This sets the delay between retries for the role.|

## Data Structure

### Bulk Host Variables

|Variable Name|Default Value|Required|Type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`jobs`|""|yes|list|List of jobs and job options to launch. Documented below|
|`description`|""|no|str|Optional description of this bulk job.|
|`organization`|""|no|str|Organization for the bulk job. Affects who can see the resulting bulk job. If not provided, will use the organization the user is in.|
|`inventory`|""|no|str|Inventory to use for the job, only used if prompt for inventory is set.|
|`scm_branch`|""|no|str|A specific of the SCM project to run the template on.|
|`extra_vars`|""|no|dict|extra_vars to use for the Job Template. ask_extra_vars needs to be set to True via controller_job_template module.|
|`limit`|""|no|str|Limit to use for the job_template.|
|`job_tags`|""|no|str|Specific tags to use for from playbook.|
|`skip_tags`|""|no|str|Specific tags to skip from the playbook.|
|`wait`|""|no|bool|Wait for the job to complete.|
|`interval`|2|no|float|The interval to request an update from controller.|

### Bulk Job Launch Sub Options

|Variable Name|Default Value|Required|Type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`unified_job_template`|""|yes|int|The ID of object that is to be launched. Example objects include projects, inventory sources, and templates. Required if state='present.|
|`inventory`|""|no|str|Inventory to use for the job, only used if prompt for inventory is set.|
|`execution_environment`|Job Template default|no|str|Execution Environment applied as a prompt. Job Template default used if not set. Only allowed if `ask_execution_environment_on_launch` set to true on Job Template|
|`instance_groups`|Job Template default|no|str| List of Instance Groups applied as a prompt. Job Template default used if not set. Only allowed if `ask_instance_groups_on_launch` set to true on Job Template|
|`credentials`|""|no|list|TCredential to use for job, only used if prompt for credential is set.|
|`labels`|Job Template default|no|list|List of labels to use in the job run. Job Template default used if not set. Only allowed if `ask_labels_on_launch` set to true on Job Template|
|`extra_data`|""|no|dict|extra_data to use for the Job Template. ask_extra_vars needs to be set to True via controller_job_template module.|
|`diff_mode`|""|no|bool|Show the changes made by Ansible tasks where supported.|
|`verbosity`|""|no|int|Verbosity level for this job run.|
|`scm_branch`|""|no|str|A specific of the SCM project to run the template on.|
|`job_type`|""|no|str|Job_type to use for the job, only used if prompt for job_type is set. Run or Check are the options.|
|`job_tags`|""|no|str|Specific tags to use for from playbook.|
|`skip_tags`|""|no|str|Specific tags to skip from the playbook.|
|`limit`|""|no|str|Limit to use for the job_template.|
|`forks`|Job Template default|no|int|Forks applied as a prompt. Job Template default used if not set. Only allowed if `ask_forks_on_launch` set to true on Job Template|
|`job_slice_count`|Job Template default|no|int|Job Slice Count to use in the job run. Job Template default used if not set. Only allowed if `ask_job_slice_count_on_launch` set to true on Job Template|
|`identifier`|""|yes|str|An identifier for the resulting workflow node that represents this job that is unique within its workflow. It is copied to workflow job nodes corresponding to this node. This functions the same as the name field for other resources, however if it is not set, it will be set to a random UUID4 value.|
|`timeout`|""|no|int|If waiting for the job to complete this will abort after this amount of seconds.|

### Standard Project Data Structure

#### Json Example

```json
{
}

```

#### Yaml Example

```yaml
---
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
    - {role: redhat_cop.controller_configuration.license, when: controller_license is defined}
```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Sean Sullivan](https://github.com/sean-m-sullivan)
