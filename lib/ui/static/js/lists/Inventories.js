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
        selectInstructions: 'Check the Select checkbox next to each inventory to be added, and click Finished when done. Use the green <i class=\"icon-plus\"></i> button to create a new inventory.', 
        
        fields: {
            name: {
                key: true,
                label: 'Name'
                },
            description: {
                label: 'Descriptions'
                },
            organization: {
                label: 'Organization',
                ngBind: 'inventory.summary_fields.organization.name',
                sourceModel: 'organization',
                sourceField: 'name'
                }
            },
        
        actions: {
            add: {
                icon: 'icon-plus',
                mode: 'all',             // One of: edit, select, all
                ngClick: 'addInventory()',
                class: 'btn btn-success',
                awToolTip: 'Create a new row'
                }
            },

        fieldActions: {
            edit: {
                ngClick: "editInventory(\{\{ inventory.id \}\})",
                icon: 'icon-edit',
                awToolTip: 'Edit'
                },

            delete: {
                ngClick: "deleteInventory(\{\{ inventory.id \}\},'\{\{ inventory.name \}\}')",
                icon: 'icon-remove',
                class: 'btn-danger',
                awToolTip: 'Delete'
                }
            }
        });
