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
        twoColumns: true,

        fields: {
            has_active_failures: {
                label: 'Host Status',
                control: '<div class="job-failures-\{\{ has_active_failures \}\}">' +
                    '<i class="icon-exclamation-sign"></i> Failed jobs</div>',
                type: 'custom',
                ngShow: 'has_active_failures',
                readonly: true,
                column: 1
                },
            inventory_name: {
                realName: 'name',
                label: 'Name',
                type: 'text',
                addRequired: true,
                editRequired: true,
                capitalize: false,
                column: 1
                },
            inventory_description: { 
                realName: 'description',
                label: 'Description',
                type: 'text',
                addRequired: false,
                editRequired: false,
                column: 1
                },
            organization: {
                label: 'Organization',
                type: 'lookup',
                sourceModel: 'organization',
                sourceField: 'name',
                addRequired: true,
                editRequired: true,
                ngClick: 'lookUpOrganization()',
                column: 1
                },
            variables: {
                label: 'Variables',
                type: 'textarea',
                addRequired: false,
                editRequird: false, 
                rows: 10,
                "class": "modal-input-xlarge",
                "default": "\{\}",
                awPopOver: "<p>Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.</p>" +
                    '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    '<p>View YAML examples at <a href="http://www.ansibleworks.com/docs/YAMLSyntax.html" target="_blank">ansibleworks.com</a></p>',
                dataTitle: 'Inventory Variables',
                dataPlacement: 'bottom',
                column: 2
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
                    has_active_failures: {
                        label: 'Failures',
                        showValue: false,
                        ngClick: "showEvents('\{\{ host.name \}\}', '\{\{ host.related.last_job \}\}')",
                        ngShow: "\{\{ host.has_active_failures \}\}",
                        icon: 'icon-exclamation-sign',
                        "class": 'active-failures-\{\{ host.has_active_failures \}\}',
                        text: 'Failed events',
                        searchField: 'has_active_failures',
                        searchType: 'boolean',
                        searchOptions: [{ name: "No", value: 0 }, { name: "Yes", value: 1 }]
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

