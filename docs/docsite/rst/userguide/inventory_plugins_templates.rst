.. _ir_inv_plugin_templates_reference:

Supported Inventory Plugin Templates
==============================================

.. index::
    pair: templates;inventory plugins

Upon upgrades, existing configurations will be migrated to the new format that will produce a backwards compatible inventory output. Use the templates below to help aid in migrating your inventories to the new style inventory plugin output.

.. contents::
    :local:


Amazon Web Services EC2
------------------------

.. index:: 
   pair: inventories; Amazon Web Services
   pair: inventories; aws
   pair: inventory plugins; aws

::

	compose:
 	  ansible_host: public_ip_address
 	  ec2_account_id: owner_id
 	  ec2_ami_launch_index: ami_launch_index | string
 	  ec2_architecture: architecture
 	  ec2_block_devices: dict(block_device_mappings | map(attribute='device_name') | list | zip(block_device_mappings | map(attribute='ebs.volume_id') | list))
 	  ec2_client_token: client_token
 	  ec2_dns_name: public_dns_name
 	  ec2_ebs_optimized: ebs_optimized
 	  ec2_eventsSet: events | default("")
 	  ec2_group_name: placement.group_name
 	  ec2_hypervisor: hypervisor
 	  ec2_id: instance_id
 	  ec2_image_id: image_id
 	  ec2_instance_profile: iam_instance_profile | default("")
 	  ec2_instance_type: instance_type
 	  ec2_ip_address: public_ip_address
 	  ec2_kernel: kernel_id | default("")
 	  ec2_key_name: key_name
 	  ec2_launch_time: launch_time | regex_replace(" ", "T") | regex_replace("(\+)(\d\d):(\d)(\d)$", ".\g<2>\g<3>Z")
 	  ec2_monitored: monitoring.state in ['enabled', 'pending']
 	  ec2_monitoring_state: monitoring.state
 	  ec2_persistent: persistent | default(false)
 	  ec2_placement: placement.availability_zone
 	  ec2_platform: platform | default("")
 	  ec2_private_dns_name: private_dns_name
 	  ec2_private_ip_address: private_ip_address
 	  ec2_public_dns_name: public_dns_name
 	  ec2_ramdisk: ramdisk_id | default("")
 	  ec2_reason: state_transition_reason
 	  ec2_region: placement.region
 	  ec2_requester_id: requester_id | default("")
 	  ec2_root_device_name: root_device_name
 	  ec2_root_device_type: root_device_type
 	  ec2_security_group_ids: security_groups | map(attribute='group_id') | list |  join(',')
 	  ec2_security_group_names: security_groups | map(attribute='group_name') | list |  join(',')
 	  ec2_sourceDestCheck: source_dest_check | default(false) | lower | string
 	  ec2_spot_instance_request_id: spot_instance_request_id | default("")
 	  ec2_state: state.name
 	  ec2_state_code: state.code
 	  ec2_state_reason: state_reason.message if state_reason is defined else ""
 	  ec2_subnet_id: subnet_id | default("")
 	  ec2_tag_Name: tags.Name
 	  ec2_virtualization_type: virtualization_type
 	  ec2_vpc_id: vpc_id | default("")
	filters:
	  instance-state-name:
 	  - running
 	groups:
 	  ec2: true
	hostnames:
 	  - network-interface.addresses.association.public-ip
 	  - dns-name
 	  - private-dns-name
 	keyed_groups:
 	  - key: image_id | regex_replace("[^A-Za-z0-9\_]", "_")
 	    parent_group: images
 	    prefix: ''
 	    separator: ''
 	  - key: placement.availability_zone
 	    parent_group: zones
 	    prefix: ''
 	    separator: ''
 	  - key: ec2_account_id | regex_replace("[^A-Za-z0-9\_]", "_")
 	    parent_group: accounts
 	    prefix: ''
 	    separator: ''
 	  - key: ec2_state | regex_replace("[^A-Za-z0-9\_]", "_")
 	    parent_group: instance_states
 	    prefix: instance_state
 	  - key: platform | default("undefined") | regex_replace("[^A-Za-z0-9\_]", "_")
 	    parent_group: platforms
 	    prefix: platform
 	  - key: instance_type | regex_replace("[^A-Za-z0-9\_]", "_")
 	    parent_group: types
 	    prefix: type
 	  - key: key_name | regex_replace("[^A-Za-z0-9\_]", "_")
 	    parent_group: keys
 	    prefix: key
 	  - key: placement.region
 	    parent_group: regions
 	    prefix: ''
 	    separator: ''
 	  - key: security_groups | map(attribute="group_name") | map("regex_replace", "[^A-Za-z0-9\_]", "_") | list
 	    parent_group: security_groups
 	    prefix: security_group
 	  - key: dict(tags.keys() | map("regex_replace", "[^A-Za-z0-9\_]", "_") | list | zip(tags.values()
 	      | map("regex_replace", "[^A-Za-z0-9\_]", "_") | list))
 	    parent_group: tags
 	    prefix: tag
 	  - key: tags.keys() | map("regex_replace", "[^A-Za-z0-9\_]", "_") | list
 	    parent_group: tags
 	    prefix: tag
 	  - key: vpc_id | regex_replace("[^A-Za-z0-9\_]", "_")
 	    parent_group: vpcs
 	    prefix: vpc_id
 	  - key: placement.availability_zone
 	    parent_group: '{{ placement.region }}'
 	    prefix: ''
 	    separator: ''
 	plugin: amazon.aws.aws_ec2
 	use_contrib_script_compatible_sanitization: true


Google Compute Engine
----------------------

.. index:: 
   pair: inventories; Google Compute Engine
   pair: inventories; gce
   pair: inventory plugins; gce

:: 

	auth_kind: serviceaccount
	compose:
	  ansible_ssh_host: networkInterfaces[0].accessConfigs[0].natIP | default(networkInterfaces[0].networkIP)
 	  gce_description: description if description else None
 	  gce_id: id
 	  gce_image: image
 	  gce_machine_type: machineType
 	  gce_metadata: metadata.get("items", []) | items2dict(key_name="key", value_name="value")
 	  gce_name: name
 	  gce_network: networkInterfaces[0].network.name
 	  gce_private_ip: networkInterfaces[0].networkIP
 	  gce_public_ip: networkInterfaces[0].accessConfigs[0].natIP | default(None)
 	  gce_status: status
 	  gce_subnetwork: networkInterfaces[0].subnetwork.name
 	  gce_tags: tags.get("items", [])
 	  gce_zone: zone
	hostnames:
	- name
	- public_ip
	- private_ip
	keyed_groups:
	- key: gce_subnetwork
	  prefix: network
	- key: gce_private_ip
	  prefix: ''
	  separator: ''
	- key: gce_public_ip
	  prefix: ''
	  separator: ''
	- key: machineType
	  prefix: ''
	  separator: ''
	- key: zone
	  prefix: ''
	  separator: ''
	- key: gce_tags
	  prefix: tag
	- key: status | lower
	  prefix: status
	- key: image
	  prefix: ''
	  separator: ''
	plugin: google.cloud.gcp_compute
	retrieve_image_info: true
	use_contrib_script_compatible_sanitization: true


Microsoft Azure Resource Manager
---------------------------------

.. index:: 
   pair: inventories; Microsoft Azure Resource Manager
   pair: inventories; azure
   pair: inventory plugins; azure

::

	conditional_groups:
  	  azure: true
	default_host_filters: []
	fail_on_template_errors: false
	hostvar_expressions:
	  computer_name: name
	  private_ip: private_ipv4_addresses[0] if private_ipv4_addresses else None
	  provisioning_state: provisioning_state | title
	  public_ip: public_ipv4_addresses[0] if public_ipv4_addresses else None
	  public_ip_id: public_ip_id if public_ip_id is defined else None
	  public_ip_name: public_ip_name if public_ip_name is defined else None
	  tags: tags if tags else None
	  type: resource_type
	keyed_groups:
	- key: location
	  prefix: ''
	  separator: ''
	- key: tags.keys() | list if tags else []
	  prefix: ''
	  separator: ''
	- key: security_group
	  prefix: ''
	  separator: ''
	- key: resource_group
	  prefix: ''
	  separator: ''
	- key: os_disk.operating_system_type
	  prefix: ''
	  separator: ''
	- key: dict(tags.keys() | map("regex_replace", "^(.*)$", "\1_") | list | zip(tags.values() | list)) if tags else []
	  prefix: ''
	  separator: ''
	plain_host_names: true
	plugin: azure.azcollection.azure_rm
	use_contrib_script_compatible_sanitization: true

VMware vCenter
---------------

.. index:: 
   pair: inventories; VMware vCenter
   pair: inventories; vmware
   pair: inventory plugins; vmware

::

	compose:
  	  ansible_host: guest.ipAddress
  	  ansible_ssh_host: guest.ipAddress
  	  ansible_uuid: 99999999 | random | to_uuid
  	  availablefield: availableField
  	  configissue: configIssue
  	  configstatus: configStatus
  	  customvalue: customValue
  	  effectiverole: effectiveRole
  	  guestheartbeatstatus: guestHeartbeatStatus
  	  layoutex: layoutEx
  	  overallstatus: overallStatus
  	  parentvapp: parentVApp
  	  recenttask: recentTask
  	  resourcepool: resourcePool
  	  rootsnapshot: rootSnapshot
  	  triggeredalarmstate: triggeredAlarmState
	filters:
	- runtime.powerState == "poweredOn"
	keyed_groups:
	- key: config.guestId
  	  prefix: ''
  	  separator: ''
	- key: '"templates" if config.template else "guests"'
  	  prefix: ''
  	  separator: ''
	plugin: community.vmware.vmware_vm_inventory
	properties:
	- availableField
	- configIssue
	- configStatus
	- customValue
	- datastore
	- effectiveRole
	- guestHeartbeatStatus
	- layout
	- layoutEx
	- name
	- network
	- overallStatus
	- parentVApp
	- permission
	- recentTask
	- resourcePool
	- rootSnapshot
	- snapshot
	- triggeredAlarmState
	- value
	- capability
	- config
	- guest
	- runtime
	- storage
	- summary
	strict: false
	with_nested_properties: true   


.. _ir_plugin_satellite:

Red Hat Satellite 6
---------------------

.. index:: 
   pair: inventories; Red Hat Satellite 6 
   pair: inventories; satellite
   pair: inventory plugins; satellite

::

	group_prefix: foreman_
	keyed_groups:
	- key: foreman['environment_name'] | lower | regex_replace(' ', '') | regex_replace('[^A-Za-z0-9_]', '_') | regex_replace('none', '')
  	  prefix: foreman_environment_
  	  separator: ''
	- key: foreman['location_name'] | lower | regex_replace(' ', '') | regex_replace('[^A-Za-z0-9_]', '_')
  	  prefix: foreman_location_
  	  separator: ''
	- key: foreman['organization_name'] | lower | regex_replace(' ', '') | regex_replace('[^A-Za-z0-9_]', '_')
  	  prefix: foreman_organization_
  	  separator: ''
	- key: foreman['content_facet_attributes']['lifecycle_environment_name'] | lower | regex_replace(' ', '') | regex_replace('[^A-Za-z0-9_]', '_')
  	  prefix: foreman_lifecycle_environment_
  	  separator: ''
	- key: foreman['content_facet_attributes']['content_view_name'] | lower | regex_replace(' ', '') | regex_replace('[^A-Za-z0-9_]', '_')
  	  prefix: foreman_content_view_
  	  separator: ''
	legacy_hostvars: true
	plugin: theforeman.foreman.foreman
	validate_certs: false
	want_facts: true
	want_hostcollections: false
	want_params: true


OpenStack
----------

.. index:: 
   pair: inventories; OpenStack
   pair: inventories; OpenStack
   pair: inventory plugins; OpenStack

::

	expand_hostvars: true
	fail_on_errors: true
	inventory_hostname: uuid
	plugin: openstack.cloud.openstack


Red Hat Virtualization
-----------------------

.. index:: 
   pair: inventories; Red Hat Virtualization 
   pair: inventories; rhv
   pair: inventory plugins; rhv

::

	compose:
  	  ansible_host: (devices.values() | list)[0][0] if devices else None
	keyed_groups:
	- key: cluster
  	  prefix: cluster
  	  separator: _
	- key: status
  	  prefix: status
  	  separator: _
	- key: tags
  	  prefix: tag
  	  separator: _
	ovirt_hostname_preference:
	- name
	- fqdn
	ovirt_insecure: false
	plugin: ovirt.ovirt.ovirt


Red Hat Ansible Automation Platform
----------------------------------------

.. index:: 
   pair: inventories; Red Hat Ansible Automation Platform
   pair: inventory plugins; Red Hat Ansible Automation Platform

::

	include_metadata: true
	inventory_id: <inventory_id or url_quoted_named_url>
	plugin: awx.awx.tower
	validate_certs: <true or false>