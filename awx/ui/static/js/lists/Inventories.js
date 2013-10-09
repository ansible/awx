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
                label: 'Description', 
                link: true
                },
            hosts_with_active_failures: {
                label: 'Hosts with<br>Failed Job?',
                ngHref: '/#/inventories/{{ inventory.id }}/hosts{{ inventory.active_failures_params }}', 
                type: 'badgeCount',
                "class": "{{ 'failures-' + inventory.has_active_failures }}",
                awToolTip: '# of hosts with failed jobs. Click to view hosts.',
                dataPlacement: 'top',
                searchable: false
                },
            inventory_sources: {
                label: 'External<br>Sources?',
                ngHref: '\{\{ inventory.has_inv_sources_link \}\}',
                badgeNgHref: '\{\{ inventory.has_inv_sources_link \}\}', 
                badgeIcon: "\{\{ 'icon-cloud-' + inventory.has_inventory_sources \}\}",
                badgePlacement: 'left',
                badgeToolTip: "\{\{ inventory.has_inv_sources_tip \}\}",
                awToolTip: "\{\{ inventory.has_inv_sources_tip \}\}",
                dataPlacement: "top",
                badgeTipPlacement: 'top',
                searchable: false,
                nosort: true
                },
            organization: {
                label: 'Organization',
                ngBind: 'inventory.summary_fields.organization.name',
                linkTo: '/#/organizations/{{ inventory.organization }}',
                sourceModel: 'organization',
                sourceField: 'name',
                excludeModal: true
                },
            has_inventory_sources: {
                label: 'Has external sources?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
                },   
            has_active_failures: {
                label: 'Has hosts with failed jobs?',
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
