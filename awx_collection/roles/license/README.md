# controller_configuration.license

## Description

An Ansible Role to deploy a license on Ansible Controller.

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
|`controller_license`|`see below`|yes|Data structure describing your license for controller, described below.||

### Secure Logging Variables

The following Variables compliment each other.
If Both variables are not set, secure logging defaults to false.
The role defaults to False as normally the add license task does not include sensitive information.
controller_configuration_license_secure_logging defaults to the value of controller_configuration_secure_logging if it is not explicitly called. This allows for secure logging to be toggled for the entire suite of controller configuration roles with a single variable, or for the user to selectively use it.

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`controller_configuration_license_secure_logging`|`False`|no|Whether or not to include the sensitive license role tasks in the log. Set this value to `True` if you will be providing your sensitive values from elsewhere.|
|`controller_configuration_secure_logging`|`False`|no|This variable enables secure logging as well, but is shared across multiple roles, see above.|

## Data Structure

### Manifest vs Subscription

The module and this role can use either a manifest file, or lookup the subscription on your account. Only one method is needed, provide the appropriate variables to use the either method.

### License Variables for using mainfest

|Variable Name|Default Value|Required|Type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`manifest_file`|""|no|obj|File path to a Red Hat subscription manifest (a .zip file)|
|`manifest_url`|""|no|obj|URL containing a Red Hat subscription manifest (a .zip file)|
|`manifest_content`|""|no|obj|Base64 encoded content of Red Hat subscription manifest|
|`manifest`|""|no|obj|DEPRECATED - changed to `manifest_file` (still works as an alias)|
|`manifest_username`|""|no|obj|Optional username for access to `manifest_url`|
|`manifest_password`|""|no|obj|Optional password for access to `manifest_url`|
|`pool_id`|""|no|str|Red Hat or Red Hat Satellite pool_id to attach to|
|`eula_accepted`|""|yes|bool|DEPRECATED since Tower 3.8 - Whether to accept the End User License Agreement for Ansible controller|
|`force`|`False`|no|bool|By default, the license manifest will only be applied if controller is currently unlicensed or trial licensed. When force=true, the license is always applied.|
|`state`|`present`|no|str|Desired state of the resource.|

For further details on fields see <https://docs.ansible.com/automation-controller/latest/html/userguide/credential_plugins.html>

### License Variables for using Red Hat Subscription

|Variable Name|Default Value|Required|Type|Description|
|:---:|:---:|:---:|:---:|:---:|
|`redhat_subscription_username`|""|no|str|Red Hat or Red Hat Satellite username to get available subscriptions.|
|`redhat_subscription_password`|""|no|str|Red Hat or Red Hat Satellite password to get available subscriptions.|
|`filters`|"default values"|no|str|dict of filters to use to narrow the subscription. See example below for how to use this.|
|`support_level`|"Self-Support"|no|str|DEPRECATED - changed to `manifest_file` (still works as an alias)|
|`list_num`|0|no|int|List index of the subscription to use, if you want to overide the default, it is recomended to use the filters to limit the pools found.|
|`pool_id`|""|no|str|Red Hat or Red Hat Satellite pool_id to attach to, setting this will skip the lookup.|
|`force`|`False`|no|bool|By default, the license will only be applied if controller is currently unlicensed or trial licensed. When force=true, the license is always applied.|
|`state`|`present`|no|str|Desired state of the resource.|

For further details on fields see <https://docs.ansible.com/automation-controller/latest/html/userguide/credential_plugins.html>

### Standard Project Data Structure

#### Json Example

```json
{
    "controller_license": {
        "manifest_file": "/tmp/my_controller.license",
        "force": true
      }
}
```

#### Yaml Example

```yaml
---
controller_license:
  manifest_url: "https://fileserver.internal/controller_license.zip"
  manifest_username: admin
  manifest_password: password
  force: false
```

## Playbook Examples

### Standard Manifest Role Usage

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
    - {role: infra.controller_configuration.license, when: controller_license is defined}
```

### Standard Subscription lookup Role Usage

```yaml
---
- name: Playbook to configure ansible controller post installation
  hosts: localhost
  connection: local
  vars:
    controller_validate_certs: false
    controller_hostname: controller.example.com
    controller_username: admin
    controller_password: changeme
    redhat_subscription_username: changeme
    redhat_subscription_password: changeme

  roles:
    - {role: infra.controller_configuration.license}
```

## License

[MIT](https://github.com/redhat-cop/controller_configuration#licensing)

## Author

[Tom Page](https://github.com/Tompage1994)
