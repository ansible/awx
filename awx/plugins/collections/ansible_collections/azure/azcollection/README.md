# Ansible collection for Azure

[![Doc](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://docs.ansible.com/ansible/latest/modules/list_of_cloud_modules.html#azure)
[![Code of conduct](https://img.shields.io/badge/code%20of%20conduct-Ansible-silver.svg)](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
[![License](https://img.shields.io/badge/license-GPL%20v3.0-brightgreen.svg)](LICENSE)

This collection provides a series of Ansible modules and plugins for interacting with the [Azure](https://azure.microsoft.com).

## Requirements

- ansible version >= 2.9

## Installation

To install Azure collection hosted in Galaxy:

```bash
ansible-galaxy collection install azure.azcollection
```

To upgrade to the latest version of Azure collection:

```bash
ansible-galaxy collection install azure.azcollection --force
```

## Usage

### Playbooks

To use a module from Azure collection, please reference the full namespace, collection name, and modules name that you want to use:

```yaml
---
- name: Using Azure collection
  hosts: localhost
  tasks:
    - azure.azcollection.azure_rm_storageaccount:
        resource_group: myResourceGroup
        name: myStorageAccount
        account_type: Standard_LRS
```

Or you can add full namepsace and collecton name in the `collections` element:

```yaml
---
- name: Using Azure collection
  hosts: localhost
  collections:
    - azure.azcollection
  tasks:
    - azure_rm_storageaccount:
        resource_group: myResourceGroup
        name: myStorageAccount
        account_type: Standard_LRS
```

### Roles

For existing Ansible roles, please also reference the full namespace, collection name, and modules name which used in tasks instead of just modules name.

### Plugins

To use a pluign from Azure collection, please reference the full namespace, collection name, and plugins name that you want to use:

```yaml
plugin: azure.azcollection.azure_rm
    include_vm_resource_groups:
    - ansible-inventory-test-rg
    auth_source: auto
````

## Resource Supported

### Modules

- azure_rm_deployment - Create or destroy Azure Resource Manager template deployments
- azure_rm_dnsrecordset - Create, delete and update DNS record sets and records
- azure_rm_dnsrecordset_info - Get DNS Record Set facts
- azure_rm_dnszone - Manage Azure DNS zones
- azure_rm_dnszone_info - Get DNS zone facts
- azure_rm_networkinterface - Manage Azure network interfaces
- azure_rm_networkinterface_info - Get network interface facts
- azure_rm_publicipaddress - Manage Azure Public IP Addresses
- azure_rm_publicipaddress_info - Get public IP facts
- azure_rm_securitygroup - Manage Azure network security groups
- azure_rm_securitygroup_info - Get security group facts
- azure_rm_storageaccount - Manage Azure storage accounts
- azure_rm_storageaccount_info - Get storage account facts
- azure_rm_subnet - Manage Azure subnets
- azure_rm_virtualmachine - Manage Azure virtual machines
- azure_rm_virtualmachine_info - Get virtual machine facts
- azure_rm_virtualnetwork - Manage Azure virtual networks
- azure_rm_virtualnetwork_info - Get virtual network facts

### Plugins

- azure_rm - Azure Resource Manager inventory plugin. Documentation [here](https://docs.ansible.com/ansible/latest/plugins/inventory/azure_rm.html) 

## Contributing

There are many ways in which you can participate in the project, for example:

- Submit bugs and feature requests, and help us verify as they are checked in
- Review source code changes
- Review the documentation and make pull requests for anything from typos to new content
- If you are interested in fixing issues and contributing directly to the code base, please see the [CONTRIBUTING](CONTRIBUTING.md) document

## License

GNU General Public License v3.0

See [LICENSE](LICENSE) to see the full text.
