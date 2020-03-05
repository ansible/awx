oVirt ansible collection
====================================

The `ovirt.ovirt_collection` manages all ansible modules of oVirt.

Note
----
Please note that when installing this collection from Ansible Galaxy you are instructed to run following command:

```bash
$ ansible-galaxy collection install ovirt.ovirt_collection
```


Requirements
------------

 * Ansible version 2.9 or higher
 * Python SDK version 4.3 or higher

Modules documentation
--------------
https://docs.ansible.com/ansible/latest/modules/list_of_cloud_modules.html#ovirt

Dependencies
------------

None.

Example Playbook
----------------

```yaml
---
- name: oVirt ansible collection
  hosts: localhost
  connection: local
  vars_files:
    # Contains encrypted `engine_password` varibale using ansible-vault
    - passwords.yml
  tasks:
    - name: Login
      ovirt_auth:
          url: "https://ovirt-engine.example.com/ovirt-engine/api"
          password: "{{ engine_password | default(omit) }}"
          username: "admin@internal"
    - name: Create vm
      ovirt_vm:
        auth: "{{ ovirt_auth }}"
        name: vm_name
        state: present
        cluster: Default
  collections:
    - ovirt.ovirt_collection
```
License
-------

Apache License 2.0
