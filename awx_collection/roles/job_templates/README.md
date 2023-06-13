# controller_configuration.job_templates

## Description

An Ansible Role to create Job Templates on Ansible Controller.

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
|`controller_templates`|`see below`|yes|Data structure describing your job template or job templates Described below. Alias: job_templates ||

### Enforcing defaults

The following Variables compliment each other.
If Both variables are not set, enforcing default values is not done.
Enabling these variables enforce default values on options that are optional in the controller API.
This should be enabled to enforce configuration and prevent configuration drift. It is recomended to be enabled, however it is not enforced by default.

Enabling this will enforce configurtion without specifying every option in the configuration files.

'controller_configuration_job_templates_enforce_defaults' defaults to the value of 'controller_configuration_enforce_defaults' if it is not explicitly called. This allows for enforced defaults to be toggled for the entire suite of controller configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_job_templates_enforce_defaults`|`False`|no|Whether or not to enforce default option values on only the applications role|
|`controller_configuration_enforce_defaults`|`False`|no|This variable enables enforced default values as well, but is shared across multiple roles, see above.|

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add job_template task does not include sensitive information.
controller_configuration_job_templates_secure_logging defaults to the value of controller_configuration_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_job_templates_secure_logging`|`False`|no|Whether or not to include the sensitive Job Template role tasks in the log. Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

### Asynchronous Retry Variables

The following Variables set asynchronous retries for the role.
If neither of the retries or delay or retries are set, they will default to their respective defaults.
This allows for all items to be created, then checked that the task finishes successfully.
This also speeds up the overall role.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_async_retries`|30|no|This variable sets the number of retries to attempt for the role globally.|
|`controller_configuration_job_templates_async_retries`|`{{ controller_configuration_async_retries }}`|no|This variable sets the number of retries to attempt for the role.|
|`controller_configuration_async_delay`|1|no|This sets the delay between retries for the role globally.|
|`controller_configuration_job_templates_async_delay`|`controller_configuration_async_delay`|no|This sets the delay between retries for the role.|

## Data Structure

### Job Template Variables

|Variable Name|Default Value|Required|Type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`name`|""|yes|str|Name of Job Template|
|`new_name`|""|str|no|Setting this option will change the existing name (looked up via the name field).|
|`copy_from`|""|no|str|Name or id to copy the job template from. This will copy an existing credential and change any parameters supplied.|
|`description`|`False`|no|str|Description to use for the job template.|
|`execution_environment`|""|no|str|Execution Environment to use for the job template.|
|`job_type`|`run`|no|str|The job type to use for the job template(run, check).|
|`inventory`|""|no|str|Name of the inventory to use for the job template.|
|`organization`|""|no|str|Organization the job template exists in. Used to help lookup the object, cannot be modified using this module. The Organization is inferred from the associated project|
|`project`|""|no|str|Name of the project to use for the job template.|
|`playbook`|""|no|str|Path to the playbook to use for the job template within the project provided.|
|`credentials`|""|no|list|List of credentials to use for the job template.|
|`forks`|""|no|int|The number of parallel or simultaneous processes to use while executing the playbook.|
|`limit`|""|no|str|A host pattern to further constrain the list of hosts managed or affected by the playbook|
|`verbosity`|""|no|int|Control the output level Ansible produces as the playbook runs. 0 - Normal, 1 - Verbose, 2 - More Verbose, 3 - Debug, 4 - Connection Debug .|
|`extra_vars`|""|no|dict|Specify extra_vars for the template.|
|`job_tags`|""|no|str|Comma separated list of the tags to use for the job template.|
|`force_handlers`|""|no|bool|Enable forcing playbook handlers to run even if a task fails.|
|`skip_tags`|""|no|str|Comma separated list of the tags to skip for the job template.|
|`start_at_task`|""|no|str|Start the playbook at the task matching this name.|
|`diff_mode`|""|no|bool|Enable diff mode for the job template |
|`use_fact_cache`|""|no|bool|Enable use of fact caching for the job template.|
|`host_config_key`|""|no|str|Allow provisioning callbacks using this host config key.|
|`ask_scm_branch_on_launch`|""|no|bool|Prompt user for scm branch on launch.|
|`ask_diff_mode_on_launch`|""|no|bool|Prompt user to enable diff mode show changes to files when supported by modules.|
|`ask_variables_on_launch`|""|no|bool|Prompt user for extra_vars on launch.|
|`ask_limit_on_launch`|""|no|bool|Prompt user for a limit on launch.|
|`ask_tags_on_launch`|""|no|bool|Prompt user for job tags on launch.|
|`ask_skip_tags_on_launch`|""|no|bool|Prompt user for job tags to skip on launch.|
|`ask_job_type_on_launch`|""|no|bool|Prompt user for job type on launch.|
|`ask_verbosity_on_launch`|""|no|bool|Prompt user to choose a verbosity level on launch.|
|`ask_inventory_on_launch`|""|no|bool|Prompt user for inventory on launch.|
|`ask_credential_on_launch`|""|no|bool|Prompt user for credential on launch.|
|`ask_execution_environment_on_launch`|""|no|bool|Prompt user for execution environment on launch.|
|`ask_forks_on_launch`|""|no|bool|Prompt user for forks on launch.|
|`ask_instance_groups_on_launch`|""|no|bool|Prompt user for instance groups on launch.|
|`ask_job_slice_count_on_launch`|""|no|bool|Prompt user for job slice count on launch.|
|`ask_labels_on_launch`|""|no|bool|Prompt user for labels on launch.|
|`ask_timeout_on_launch`|""|no|bool|Prompt user for timeout on launch.|
|`prevent_instance_group_fallback`|""|no|bool|Prevent falling back to instance groups set on the associated inventory or organization.|
|`survey_enabled`|""|no|bool|Enable a survey on the job template.|
|`survey_spec`|""|no|dict|JSON/YAML dict formatted survey definition.|
|`survey`|""|no|dict|JSON/YAML dict formatted survey definition. Alias of survey_spec|
|`become_enabled`|""|no|bool|Activate privilege escalation.|
|`allow_simultaneous`|""|no|bool|Allow simultaneous runs of the job template.|
|`timeout`|""|no|int|Maximum time in seconds to wait for a job to finish (server-side).|
|`instance_groups`|""|no|list|list of Instance Groups for this Job Template to run on.|
|`job_slice_count`|""|no|int|The number of jobs to slice into at runtime. Will cause the Job Template to launch a workflow if value is greater than 1.|
|`webhook_service`|""|no|str|Service that webhook requests will be accepted from (github, gitlab)|
|`webhook_credential`|""|no|str|Personal Access Token for posting back the status to the service API|
|`scm_branch`|""|no|str|Branch to use in job run. Project default used if blank. Only allowed if project allow_override field is set to true.|
|`labels`|""|no|list|The labels applied to this job template. NOTE: Labels must be created with the [labels](https://github.com/redhat-cop/controller_configuration/tree/devel/roles/labels) role first, an error will occur if the label supplied to this role does not exist.|
|`custom_virtualenv`|""|no|str|Local absolute file path containing a custom Python virtualenv to use.|
|`notification_templates_started`|""|no|list|The notifications on started to use for this organization in a list.|
|`notification_templates_success`|""|no|list|The notifications on success to use for this organization in a list.|
|`notification_templates_error`|""|no|list|The notifications on error to use for this organization in a list.|
|`state`|`present`|no|str|Desired state of the resource.|

### Surveys

Refer to the [controller Api Guide](https://docs.ansible.com/ansible-tower/latest/html/towerapi/api_ref.html#/Job_Templates/Job_Templates_job_templates_survey_spec_create) for more information about forming surveys

|Variable Name|Variable Description|
|:---:|:---:|
|`name`|Name of the survey|
|`description`|Description of the survey|
|`spec`|List of survey items, each a dictionary containing the following fields|
|`question_name`|Name of the field/item|
|`question_description`|Longer description|
|`required`|Boolean expressing if an answer is required|
|`type`|One of `text`, `password`, `integer`, `float`, `multiplechoice`or `multiselect`|
|`variable`|Name of Ansible Variable where to put the answer|
|`default`|Default value for the variable|
|`min`|Minimum value for a number type|
|`max`|Maximum value for a number type|
|`choices`|List of choices for a "multi" type|
|`new_question`|Boolean|

### Standard Project Data Structure

#### Json Example

```json
{
    "controller_templates": [
        {
            "name": "Survey Template with vars",
            "job_type": "run",
            "inventory": "Demo Inventory",
            "survey_enabled": true,
            "survey": "{{ lookup('template', 'template_surveys/basic_survey.json') | regex_replace('\\n', '') }}",
            "project": "controller Config",
            "playbook": "helloworld.yml",
            "credentials": [
                "Demo Credential"
              ],
            "extra_vars": "{{ survey_extra_vars }}",
            "notification_templates_error": [
                "Slack_for_testing"
              ]
        },
        {
            "name": "No Survey Template no vars",
            "job_type": "run",
            "inventory": "Demo Inventory",
            "project": "controller Config",
            "playbook": "helloworld.yml",
            "credentials": [
                "Demo Credential"
              ],
            "survey": {},
            "extra_vars": "{{ empty_master_vars }}",
            "notification_templates_error": [
                "Slack_for_testing"
              ]
        }
    ]
}
```

#### Yaml Example

```yaml
---
controller_templates:
- name: Survey Template with vars
  job_type: run
  inventory: Demo Inventory
  execution_environment: my_exec_env
  survey_enabled: true
  survey: "{{ lookup('template', 'template_surveys/basic_survey.json') | regex_replace('\\n', '') }}"
  project: controller Config
  playbook: helloworld.yml
  credentials:
  - Demo Credential
  extra_vars: "{{ survey_extra_vars }}"
  notification_templates_error:
  - Slack_for_testing
- name: No Survey Template no vars
  job_type: run
  inventory: Demo Inventory
  project: controller Config
  playbook: helloworld.yml
  credentials:
  - Demo Credential
  survey: {}
  extra_vars: "{{ empty_master_vars }}"
  notification_templates_error:
  - Slack_for_testing
```

### Survey Data Structure

#### Survey Json Example

```json
{
    "name": "Basic Survey",
    "description": "Basic Survey",
    "spec": [
      {
        "question_description": "Name",
        "min": 0,
        "default": "",
        "max": 128,
        "required": true,
        "choices": "",
        "new_question": true,
        "variable": "basic_name",
        "question_name": "Basic Name",
        "type": "text"
      },
      {
        "question_description": "Choosing yes or no.",
        "min": 0,
        "default": "yes",
        "max": 0,
        "required": true,
        "choices": "yes\nno",
        "new_question": true,
        "variable": "option_true_false",
        "question_name": "Choose yes or no?",
        "type": "multiplechoice"
      },
      {
        "question_description": "",
        "min": 0,
        "default": "",
        "max": 0,
        "required": true,
        "choices": "group1\ngroup2\ngroup3",
        "new_question": true,
        "variable": "target_groups",
        "question_name": "Select Group:",
        "type": "multiselect"
      }
    ]
  }
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
    - {role: awx.controller_configuration.job_templates, when: controller_templates is defined}
```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Sean Sullivan](https://github.com/sean-m-sullivan)
