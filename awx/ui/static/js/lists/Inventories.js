/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Inventories.js 
 *  List view object for Inventories data model.
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
            has_inventory_sources: {
                label: 'Cloud sourced?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
                },   
            has_active_failures: {
                label: 'Failed hosts?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
                },
            inventory_sources_with_failures: {
                label: 'Sync failures?',
                searchType: 'gtzero',
                searchValue: 'true',
                searchOnly: true
                }
            },
        
        actions: {
            add: {
                mode: 'all',             // One of: edit, select, all
                ngClick: 'addInventory()',
                awToolTip: 'Create a new inventory'
                },
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                icon: "icon-comments-alt",
                mode: 'all',
                ngShow: "user_is_superuser"
                }
            },

        fieldActions: {
             status: { 
                //label: 'Status', 
                ngHref: "\{\{ inventory.status_link \}\}",
                iconClass: "\{\{ 'fa fa-cloud icon-cloud-' + inventory.status_class \}\}",
                awToolTip: "\{\{ inventory.status_tip \}\}",
                dataPlacement: "top"
                },
             failed_hosts: {
                //label: 'Failures',
                ngHref: "\{\{ inventory.failed_hosts_link \}\}",
                iconClass: "\{\{ 'fa icon-failures-' + inventory.failed_hosts_class \}\}",
                awToolTip: "\{\{ inventory.failed_hosts_tip \}\}",
                dataPlacement: "top"
                },
            edit: {
                label: 'Edit',
                ngClick: 'editInventoryProperties(inventory.id)',
                awToolTip: 'Edit inventory',
                dataPlacement: 'top'
                },
            "delete": {
                label: 'Delete',
                ngClick: "deleteInventory(\{\{ inventory.id \}\},'\{\{ inventory.name \}\}')",
                awToolTip: 'Delete inventory',
                dataPlacement: 'top'
                }
             /*,
             dropdown: {
                type: 'DropDown',
                label: 'Jobs',
                icon: 'icon-zoom-in',
                'class': 'btn-default btn-xs',
                options: [
                    { ngClick: 'viewJobs(\{\{ inventory.id \}\})', label: 'All' },
                    { ngClick: "viewFailedJobs(\{\{ inventory.id \}\})", label: 'Failed' }
                    ]
                }
                */
            }
        });
