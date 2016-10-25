/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('InventoriesListDefinition', [])
    .factory('InventoryList', ['i18n', function(i18n) {
    return {

        name: 'inventories',
        iterator: 'inventory',
        selectTitle: i18n._('Add Inventories'),
        editTitle: i18n._('Inventories'),
        listTitle: i18n._('Inventories'),
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
                    awToolTip: false,
                    ngClick: "showHostSummary($event, inventory.id)",
                    ngClass: ""
                }]
            },
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-md-5 col-sm-5 col-xs-8 List-staticColumnAdjacent',
                modalColumnClass: 'col-md-11',
                linkTo: '/#/inventories/{{inventory.id}}/manage'
            },
            organization: {
                label: i18n._('Organization'),
                ngBind: 'inventory.summary_fields.organization.name',
                linkTo: '/#/organizations/{{ inventory.organization }}',
                sourceModel: 'organization',
                sourceField: 'name',
                excludeModal: true,
                columnClass: 'col-md-5 col-sm-3 hidden-xs'
            },
            has_inventory_sources: {
                label: i18n._('Cloud sourced?'),
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
            },
            has_active_failures: {
                label: i18n._('Failed hosts?'),
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
            },
            inventory_sources_with_failures: {
                label: i18n._('Sync failures?'),
                searchType: 'select',
                searchOptions: [{
                    label: i18n._('Yes'),
                    value: 'inventory_sources_with_failures__gt=0'
                }, {
                    label: i18n._('No'),
                    value: 'inventory_sources_with_failures__lte=0'
                }],
                searchOnly: true
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addInventory()',
                awToolTip: i18n._('Create a new inventory'),
                actionClass: 'btn List-buttonSubmit',
                buttonContent: i18n._('&#43; ADD'),
                ngShow: 'canAdd'
            }
        },

        fieldActions: {

            columnClass: 'col-md-2 col-sm-4 col-xs-4',

            edit: {
                label: i18n._('Edit'),
                ngClick: 'editInventory(inventory.id)',
                awToolTip: i18n._('Edit inventory'),
                dataPlacement: 'top',
                ngShow: 'inventory.summary_fields.user_capabilities.edit'
            },
            view: {
                label: i18n._('View'),
                ngClick: 'editInventory(inventory.id)',
                awToolTip: i18n._('View inventory'),
                dataPlacement: 'top',
                ngShow: '!inventory.summary_fields.user_capabilities.edit'
            },
            "delete": {
                label: i18n._('Delete'),
                ngClick: "deleteInventory(inventory.id, inventory.name)",
                awToolTip: i18n._('Delete inventory'),
                dataPlacement: 'top',
                ngShow: 'inventory.summary_fields.user_capabilities.delete'
            }
        }
    };}]);
