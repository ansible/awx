/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Inventories.js 
 *  List view object for Inventories data model.
 *
 * 
 */
angular.module('InventoriesListDefinition', [])
    .value(
    'InventoryList', {
        
        name: 'inventories',
        iterator: 'inventory',
        selectTitle: 'Add Inventories',
        editTitle: 'Inventories',
        selectInstructions: 'Click on a row to select it, and click Finished when done. Use the green <i class=\"icon-plus\"></i> button to create a new row.', 
        index: true,
        hover: true,
        
        fields: {
            name: {
                key: true,
                label: 'Name',
                badgeIcon: "\{\{ 'icon-failures-' + inventory.has_active_failures \}\}",
                badgePlacement: 'left'
                },
            description: {
                label: 'Description'
                },
            organization: {
                label: 'Organization',
                ngBind: 'inventory.summary_fields.organization.name',
                sourceModel: 'organization',
                sourceField: 'name',
                excludeModal: true
                }
            },
        
        actions: {
            add: {
                label: 'Create New',
                icon: 'icon-plus',
                mode: 'all',             // One of: edit, select, all
                ngClick: 'addInventory()',
                "class": 'btn-sm btn-success',
                awToolTip: 'Create a new inventory'
                }
            },

        fieldActions: {
            
            dropdown: {
                type: 'DropDown',
                label: 'View Jobs',
                'class': 'btn-xs',
                options: [
                    { ngClick: 'viewJobs(\{\{ inventory.id \}\})', label: 'Jobs' },
                    { ngClick: "viewFailedJobs(\{\{ inventory.id \}\})", label: 'Failed jobs' }
                    ]
                },

            hosts: {
                label: 'Hosts',
                ngClick: "editHosts(\{\{ inventory.id \}\})",
                icon: 'icon-th-large',
                "class": 'btn-xs btn-default',
                awToolTip: 'Edit Hosts'
                },

            groups: {
                label: 'Groups',
                ngClick: "editGroups(\{\{ inventory.id \}\})",
                icon: 'icon-group',
                "class": 'btn-xs btn-default',
                awToolTip: 'Edit Groups'
                },

            edit: {
                ngClick: "editInventory(\{\{ inventory.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-xs btn-default',
                awToolTip: 'Edit Inventory Properties'
                },

            "delete": {
                ngClick: "deleteInventory(\{\{ inventory.id \}\},'\{\{ inventory.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-xs btn-danger',
                awToolTip: 'Delete inventory'
                }
            }
        });
