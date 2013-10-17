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
            organization: {
                label: 'Organization',
                ngBind: 'inventory.summary_fields.organization.name',
                linkTo: '/#/organizations/{{ inventory.organization }}',
                sourceModel: 'organization',
                sourceField: 'name',
                excludeModal: true
                },
            failed_hosts: {
                label: 'Failed Hosts',
                ngHref: "\{\{ inventory.failed_hosts_link \}\}",
                badgeIcon: "\{\{ 'icon-failures-' + inventory.failed_hosts_class \}\}",
                badgeNgHref: "\{\{ inventory.failed_hosts_link \}\}",
                badgePlacement: 'left',
                badgeToolTip: "\{\{ inventory.failed_hosts_tip \}\}",
                badgeTipPlacement: 'top',
                awToolTip: "\{\{ inventory.failed_hosts_tip \}\}",
                dataPlacement: "top",
                searchable: false,
                excludeModal: true,
                sortField: "hosts_with_active_failures"
                },
            status: { 
                label: 'Status', 
                ngHref: "\{\{ inventory.status_link \}\}",
                badgeIcon: "\{\{ 'icon-cloud-' + inventory.status_class \}\}",
                badgeNgHref: "\{\{ inventory.status_link \}\}",
                badgePlacement: 'left',
                badgeTipPlacement: 'top',
                badgeToolTip: "\{\{ inventory.status_tip \}\}",
                awToolTip: "\{\{ inventory.status_tip \}\}",
                dataPlacement: "top",
                searchable: false,
                excludeModal: true,
                sortField: "inventory_sources_with_failures"
                },
            has_inventory_sources: {
                label: 'Has external sources?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
                },   
            has_active_failures: {
                label: 'Has failed hosts?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
                }
            },
        
        actions: {
            add: {
                label: 'Create New',
                icon: 'icon-plus',
                mode: 'all',             // One of: edit, select, all
                ngClick: 'addInventory()',
                "class": 'btn-xs btn-success',
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
                    { ngClick: 'viewJobs(\{\{ inventory.id \}\})', label: 'All' },
                    { ngClick: "viewFailedJobs(\{\{ inventory.id \}\})", label: 'Failed' }
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
