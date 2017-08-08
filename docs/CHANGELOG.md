3.2.0
=====
* added a new API endpoint - `/api/v1/settings/logging/test/` - for testing
  external log aggregrator connectivity
  [[#5164](https://github.com/ansible/ansible-tower/issues/5164)]
* allow passing `-e create_preload_data=False` to skip creating default
  organization/project/inventory/credential/job_template during Tower
  installation
  [[#5746](https://github.com/ansible/ansible-tower/issues/5746)]
* removed links from group to `inventory_source` including the field and
  related links, removed `start` and `schedule` capabilities from
  group serializer and added `user_capabilities` to inventory source
  serializer, allow user creation and naming of inventory sources
  [[#5741](https://github.com/ansible/ansible-tower/issues/5741)]
* support sourcing inventory from a file inside of a project's source
  tree [[#2477](https://github.com/ansible/ansible-tower/issues/2477)]
* added support for custom cloud and network credential types, which give the
  customer the ability to modify environment variables, extra vars, and
  generate file-based credentials (such as file-based certificates or .ini
  files) at `ansible-playbook` runtime
  [[#5876](https://github.com/ansible/ansible-tower/issues/5876)]
* added support for assigning multiple cloud and network credential types on
  `JobTemplates`.  ``JobTemplates`` can prompt for "extra credentials" at
  launch time in the same manner as promptable machine credentials
  [[#5807](https://github.com/ansible/ansible-tower/issues/5807)]
  [[#2913](https://github.com/ansible/ansible-tower/issues/2913)]
* custom inventory sources can now specify a ``Credential``; you
  can store third-party credentials encrypted within Tower and use their
  values from within your custom inventory script (by - for example - reading
  an environment variable or a file's contents)
  [[#5879](https://github.com/ansible/ansible-tower/issues/5879)]
* Added support for configuring groups of instance nodes to run tower
  jobs [[#5898](https://github.com/ansible/ansible-tower/issues/5898)]
* Fixed an issue installing Tower on multiple nodes where cluster
  internal node references are used
  [[#6231](https://github.com/ansible/ansible-tower/pull/6231)]
* Tower now uses a modified version of [Fernet](https://github.com/fernet/spec/blob/master/Spec.md).
  Our `Fernet256` class uses `AES-256-CBC` instead of `AES-128-CBC` for all encrypted fields.
  [[#826](https://github.com/ansible/ansible-tower/issues/826)]
* Added the ability to set custom environment variables set for playbook runs,
  inventory updates, project updates, and notification sending.
  [[#3508](https://github.com/ansible/ansible-tower/issues/3508)]
* Added --diff mode to Job Templates and Ad-Hoc Commands.  The diff can be found in the
  standard out when diff mode is enabled.  [[#4525](https://github.com/ansible/ansible-tower/issues/4325)]
* Support accessing some Tower resources via their name-related unique identifiers apart from primary keys.
(named URL) [[#3362](https://github.com/ansible/ansible-tower/issues/3362)]
* Support TACACS+ authentication. [[#3400](https://github.com/ansible/ansible-tower/issues/3400)]
* Support sending system logs to external log aggregators via direct TCP/UDP connection.
[[#5783](https://github.com/ansible/ansible-tower/pull/5783)]
* Remove Rackspace as a supported inventory source type and credential type.
[[#6117](https://github.com/ansible/ansible-tower/pull/6117)]
* Changed names of tower-mange commands `register_instance` -> `provision_instance`,
  `deprovision_node` -> `deprovision_instance`, and `instance_group_remove` -> `remove_from_queue`,
  which backward compatibility support for 3.1 use pattern
  [[#6915](https://github.com/ansible/ansible-tower/issues/6915)]
