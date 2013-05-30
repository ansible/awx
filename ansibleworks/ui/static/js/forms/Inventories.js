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
        
        addTitle: 'Create Inventory',                             //Legend in add mode
        editTitle: '{{ name }}',                                  //Legend in edit mode
        name: 'inventory',
        well: true,
        collapse: true,
        collapseTitle: 'Edit Inventory',
        collapseMode: 'edit',

        fields: {
            name: {
                label: 'Name',
                type: 'text',
                addRequired: true,
                editRequired: true,
                capitalize: true
                },
            description: { 
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
                class: 'btn-success',
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
                title: "{{ groupName }}",
                iterator: 'host',
                actions: { 
                    add: {
                        ngClick: "add('hosts')",
                        icon: 'icon-plus',
                        label: 'Add',
                        awToolTip: 'Create a new host',
                        ngHide: 'createButtonShow == false'
                        },
                    },
                
                fields: {
                    name: {
                        key: true,
                        label: 'Name',
                        linkTo: "/inventories/\{\{ inventory_id \}\}/hosts/\{\{ host.id \}\}"
                        },
                    description: {
                        label: 'Description'
                        }
                    },
                
                fieldActions: {
                    edit: {
                        ngClick: "edit('hosts', \{\{ host.id \}\}, '\{\{ host.name \}\}')",
                        icon: 'icon-edit',
                        label: 'Edit',
                        class: 'btn-success',
                        awToolTip: 'Edit host'
                        },
                    delete: {
                        ngClick: "delete('hosts', \{\{ host.id \}\}, '\{\{ host.name \}\}', 'hosts')",
                        icon: 'icon-remove',
                        label: 'Delete',
                        class: 'btn-danger',
                        awToolTip: 'Remove host'
                        }
                    }    
                }
            }

    }); //InventoryForm

