/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 

export default
    angular.module('InventoriesListDefinition', [])
    .value('InventoryList', {

        name: 'inventories',
        iterator: 'inventory',
        selectTitle: 'Add Inventories',
        editTitle: 'Inventories',
        selectInstructions: "Click on a row to select it, and click Finished when done. Click the <i class=\"icon-plus\"></i> " +
            "button to create a new inventory.",
        index: false,
        hover: true,

        fields: {
            status: {
                label: 'Status',
                columnClass: 'col-md-2 col-sm-2 col-xs-2',
                searchable: false,
                nosort: true,
                ngClick: "null",
                iconOnly: true,
                excludeModal: true,
                icons: [{
                    icon: "{{ 'icon-cloud-' + inventory.syncStatus }}",
                    awToolTip: "{{ inventory.syncTip }}",
                    awTipPlacement: "top",
                    ngClick: "showGroupSummary($event, inventory.id)",
                    ngClass: "inventory.launch_class"
                },{
                    icon: "{{ 'icon-job-' + inventory.hostsStatus }}",
                    awToolTip: "{{ inventory.hostsTip }}",
                    awTipPlacement: "top",
                    ngClick: "showHostSummary($event, inventory.id)",
                    ngClass: ""
                }]
            },
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-md-4 col-sm-6 col-xs-6',
                modalColumnClass: 'col-md-8',
                linkTo: '/#/inventories/{{inventory.id}}/manage'
            },
            organization: {
                label: 'Organization',
                ngBind: 'inventory.summary_fields.organization.name',
                linkTo: '/#/organizations/{{ inventory.organization }}',
                sourceModel: 'organization',
                sourceField: 'name',
                excludeModal: true,
                columnClass: 'col-md-4 hidden-sm hidden-xs'
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
                mode: 'all', // One of: edit, select, all
                ngClick: 'addInventory()',
                awToolTip: 'Create a new inventory'
            },
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                icon: "icon-comments-alt",
                mode: 'edit',
                awFeature: 'activity_streams'
            }
        },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: 'editInventory(inventory.id)', //'editInventoryProperties(inventory.id)',
                awToolTip: 'Edit inventory',
                dataPlacement: 'top'
            },
            "delete": {
                label: 'Delete',
                ngClick: "deleteInventory(inventory.id, inventory.name)",
                awToolTip: 'Delete inventory',
                dataPlacement: 'top'
            }
        }
    });
