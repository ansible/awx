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
* Added support for configuring groups of instance nodes to run tower
  jobs [[#5898](https://github.com/ansible/ansible-tower/issues/5898)]
* Fixed an issue installing Tower on multiple nodes where cluster
  internal node references are used
  [[#6231](https://github.com/ansible/ansible-tower/pull/6231)]
