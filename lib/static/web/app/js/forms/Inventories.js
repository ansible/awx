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
                addRequired: true,
                editRequired: true
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
                class: 'btn btn-success',
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: true          //Disable when $pristine or $invalid, optional
                },
            reset: { 
                ngClick: 'formReset()',
                label: 'Reset',
                icon: 'icon-remove',
                class: 'btn',
                ngDisabled: true          //Disabled when $pristine
                }
            },

        related: { //related colletions (and maybe items?)

             hosts:  {
                type: 'collection',
                title: 'Hosts',
                iterator: 'host',
                open: false,
                
                actions: { 
                    add: {
                        ngClick: "add('hosts')",
                        icon: 'icon-plus'
                        },
                    },
                
                fields: {
                    name: {
                        key: true,
                        label: 'Name'
                        },
                    description: {
                        label: 'Description'
                        }
                    },
                
                fieldActions: {
                    edit: {
                        ngClick: "edit('hosts', \{\{ host.id \}\}, '\{\{ host.name \}\}')",
                        icon: 'icon-edit'
                        },
                    delete: {
                        ngClick: "delete('hosts', \{\{ host.id \}\}, '\{\{ host.name \}\}', 'hosts')",
                        icon: 'icon-remove',
                        class: 'btn-danger'
                        }
                    }
                } 
            }
    }); //InventoryForm

