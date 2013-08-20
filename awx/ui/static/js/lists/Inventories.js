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
                label: 'Name'
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
                },
            has_active_failures: {
                label: 'Failed Jobs?',
                showValue: false,
                text: 'View failures',
                ngShow: "\{\{ inventory.has_active_failures \}\}",
                icon: 'icon-exclamation-sign',
                "class": 'active-failures-\{\{ inventory.has_active_failures \}\}',
                ngClick: 'viewJobs(\{\{ inventory.id \}\})',
                searchField: 'has_active_failures',
                searchType: 'boolean',
                searchOptions: [{ name: "No", value: 0 }, { name: "Yes", value: 1 }],
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
            edit: {
                label: 'Edit',
                ngClick: "editInventory(\{\{ inventory.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-xs btn-default',
                awToolTip: 'View/Edit inventory'
                },

            "delete": {
                label: 'Delete',
                ngClick: "deleteInventory(\{\{ inventory.id \}\},'\{\{ inventory.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-xs btn-danger',
                awToolTip: 'Delete inventory'
                }
            }
        });
