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
        listTitle: 'Inventories',
        selectInstructions: "Click on a row to select it, and click Finished when done. Click the <i class=\"icon-plus\"></i> " +
            "button to create a new inventory.",
        index: false,
        hover: true,

        fields: {
            status: {
                label: '',
                columnClass: 'List-staticColumn--mediumStatus',
                searchable: false,
                nosort: true,
                ngClick: "null",
                iconOnly: true,
                excludeModal: true,
                icons: [{
                    icon: "{{ 'icon-cloud-' + inventory.syncStatus }}",
                    awToolTip: "{{ inventory.syncTip }}",
                    awTipPlacement: "right",
                    ngClick: "showGroupSummary($event, inventory.id)",
                    ngClass: "inventory.launch_class"
                },{
                    icon: "{{ 'icon-job-' + inventory.hostsStatus }}",
                    awToolTip: "{{ inventory.hostsTip }}",
                    awTipPlacement: "right",
                    ngClick: "showHostSummary($event, inventory.id)",
                    ngClass: ""
                }]
            },
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-md-5 col-sm-5 col-xs-8 List-staticColumnAdjacent',
                modalColumnClass: 'col-md-11',
                linkTo: '/#/inventories/{{inventory.id}}/manage'
            },
            organization: {
                label: 'Organization',
                ngBind: 'inventory.summary_fields.organization.name',
                linkTo: '/#/organizations/{{ inventory.organization }}',
                sourceModel: 'organization',
                sourceField: 'name',
                excludeModal: true,
                columnClass: 'col-md-5 col-sm-3 hidden-xs'
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
                searchType: 'select',
                searchOptions: [{
                    label: 'Yes',
                    value: 'inventory_sources_with_failures__gt=0'
                }, {
                    label: 'No',
                    value: 'inventory_sources_with_failures__lte=0'
                }],
                searchOnly: true
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addInventory()',
                awToolTip: 'Create a new inventory',
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ADD'
            }
        },

        fieldActions: {

            columnClass: 'col-md-2 col-sm-4 col-xs-4',

            edit: {
                label: 'Edit',
                ngClick: 'editInventory(inventory.id)',
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
