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
                badgePlacement: 'left',
                badgeToolTip: 'Indicates if inventory contains hosts with active failures',
                badgeTipPlacement: 'bottom'
                },
            description: {
                label: 'Description',
                link: true
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
                label: 'Jobs',
                icon: 'icon-zoom-in',
                'class': 'btn-default btn-xs',
                options: [
                    { ngClick: 'viewJobs(\{\{ inventory.id \}\})', label: 'All Jobs' },
                    { ngClick: "viewFailedJobs(\{\{ inventory.id \}\})", label: 'Failed jobs' }
                    ]
                },
            edit: { 
                type: 'DropDown', 
                label: 'Edit',
                icon: 'icon-edit',
                'class': 'btn-default btn-xs',
                options: [
                    { ngClick: "editInventory(\{\{ inventory.id \}\})", label: 'Properties' },
                    { ngClick: "editHosts(\{\{ inventory.id \}\})", label: 'Hosts' }, 
                    { ngClick: "editGroups(\{\{ inventory.id \}\})", label: 'Groups' }
                    ]
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
