#!/bin/bash

base_dir=awx/plugins/collections/ansible_collections

if [ ! -d "$base_dir/azure/azcollection" ]
then
	mkdir -p $base_dir/azure
	git clone https://github.com/ansible-collections/azure.git $base_dir/azure/azcollection
else
  echo "Azure collection already exists"
fi

if [ ! -d "$base_dir/ansible/amazon" ]
then
	mkdir -p $base_dir/ansible
	git clone https://github.com/ansible-collections/ansible.amazon.git $base_dir/ansible/amazon
else
  echo "Amazon collection already exists"
fi

if [ ! -d "$base_dir/theforeman/foreman" ]
then
	mkdir -p $base_dir/theforeman
	git clone https://github.com/theforeman/foreman-ansible-modules.git $base_dir/theforeman/foreman
else
  echo "foreman collection already exists"
fi

if [ ! -d "$base_dir/google/cloud" ]
then
	mkdir -p $base_dir/google
	git clone https://github.com/ansible-collections/ansible_collections_google.git $base_dir/google/cloud
else
  echo "google collection already exists"
fi

if [ ! -d "$base_dir/openstack/cloud" ]
then
	mkdir -p $base_dir/openstack
	git clone https://github.com/openstack/ansible-collections-openstack.git $base_dir/openstack/cloud
else
  echo "openstack collection already exists"
fi

if [ ! -d "$base_dir/community/vmware" ]
then
	mkdir -p $base_dir/community
	git clone https://github.com/ansible-collections/vmware.git $base_dir/community/vmware
else
  echo "VMWare collection already exists"
fi

if [ ! -d "$base_dir/ovirt/ovirt" ]
then
	mkdir -p $base_dir/ovirt
	git clone https://github.com/oVirt/ovirt-ansible-collection.git $base_dir/ovirt/ovirt
else
  echo "Ovirt collection already exists"
fi

if [ ! -d "$base_dir/awx/awx" ]
then
	mkdir -p $base_dir/awx
  ln -s $(shell pwd)/awx_collection $base_dir/awx/awx
else
  echo "awx collection already exists"
fi

echo "-- confirmation of what is installed --"
ANSIBLE_COLLECTIONS_PATHS=awx/plugins/collections ansible-galaxy collection list
