/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Inventories.js
 *  Form definition for User model
 *
 * 
 */
angular.module('InventoryFormDefinition', [])
    .value(
    'InventoryForm', {
        
        addTitle: 'Create Inventory',
        editTitle: '{{ inventory_name }}',
        name: 'inventory',
        well: true,
        collapse: true,
        collapseTitle: 'Edit Inventory',
        collapseMode: 'edit',

        fields: {
            inventory_name: {
                realName: 'name',
                label: 'Name',
                type: 'text',
                addRequired: true,
                editRequired: true,
                capitalize: false
                },
            inventory_description: { 
                realName: 'description',
                label: 'Description',
                type: 'text',
                addRequired: false,
                editRequired: false
                },
            organization: {
                label: 'Organization',
                type: 'lookup',
                sourceModel: 'organization',
                sourceField: 'name',
                addRequired: true,
                editRequired: true,
                ngClick: 'lookUpOrganization()'
                }
            },

        buttons: { //for now always generates <button> tags 
            save: { 
                label: 'Save', 
                icon: 'icon-ok',
                "class": 'btn-success',
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: true          //Disable when $pristine or $invalid, optional
                },
            reset: { 
                ngClick: 'formReset()',
                label: 'Reset',
                icon: 'icon-remove',
                ngDisabled: true          //Disabled when $pristine
                }
            },

        related: {

            groups: {
                type: 'tree',
                open: true,
                actions: { 
                    }
                },

            hosts: {
                type: 'treeview',
                title: "{{ groupTitle }}",
                iterator: 'host',
                actions: { 
                    add: {
                        ngClick: "addHost()",
                        icon: 'icon-plus',
                        label: 'Add Host',
                        awToolTip: 'Add a host',
                        ngHide: 'createButtonShow == false'
                        }
                    },
                
                fields: {
                    name: {
                        key: true,
                        label: 'Name',
                        ngClick: "editHost(\{\{ host.id \}\}, '\{\{ host.name \}\}')"
                        },
                    description: {
                        label: 'Description'
                        }
                    },
                
                fieldActions: {
                    edit: {
                        ngClick: "editHost(\{\{ host.id \}\}, '\{\{ host.name \}\}')",
                        icon: 'icon-edit',
                        label: 'Edit',
                        "class": 'btn-success',
                        awToolTip: 'Edit host'
                        },
                    "delete": {
                        ngClick: "deleteHost(\{\{ host.id \}\}, '\{\{ host.name \}\}')",
                        icon: 'icon-remove',
                        label: 'Delete',
                        "class": 'btn-danger',
                        awToolTip: 'Remove host'
                        }
                    }    
                }
            }

    }); //InventoryForm

