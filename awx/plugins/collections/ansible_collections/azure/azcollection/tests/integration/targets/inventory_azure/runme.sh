#!/usr/bin/env bash

set -eux

# ensure test config is empty
ansible-playbook playbooks/empty_inventory_config.yml "$@"

export ANSIBLE_INVENTORY=test.azure_rm.yml

# generate inventory config and test using it
ansible-playbook playbooks/create_inventory_config.yml "$@"
ansible-playbook playbooks/test_inventory.yml "$@"

#ansible-inventory -i test.azure_rm.yml --list -vvv --playbook-dir=./

# cleanup inventory config
ansible-playbook playbooks/empty_inventory_config.yml "$@"