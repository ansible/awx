/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default ['i18n', function(i18n) {
    return {

        name: 'inventories',
        iterator: 'inventory',
        selectTitle: i18n._('Add Inventories'),
        editTitle: i18n._('INVENTORIES'),
        listTitle: i18n._('INVENTORIES'),
        selectInstructions: i18n.sprintf(i18n._("Click on a row to select it, and click Finished when done. Click the %s button to create a new inventory."), "<i class=\"icon-plus\"></i> "),
        index: false,
        hover: true,
        basePath: 'inventory',
        title: false,
        disableRow: "{{ inventory.pending_deletion }}",

        fields: {
            status: {
                label: '',
                columnClass: 'List-staticColumn--mediumStatus',
                nosort: true,
                ngClick: "null",
                iconOnly: true,
                excludeModal: true,
                template: `<source-summary-popover inventory="inventory" ng-hide="inventory.pending_deletion" ng-if="inventory.kind === ''"></source-summary-popover><host-summary-popover inventory="inventory" ng-hide="inventory.pending_deletion" ng-class="{'HostSummaryPopover-noSourceSummary': inventory.kind !== ''}"></host-summary-popover>`,
                icons: [{
                    icon: "{{ 'icon-cloud-' + inventory.syncStatus }}",
                    awToolTip: "{{ inventory.syncTip }}",
                    awTipPlacement: "right",
                    ngClick: "showSourceSummary($event, inventory.id)",
                    ngClass: "inventory.launch_class"
                },{
                    icon: "{{ 'icon-job-' + inventory.hostsStatus }}",
                    awToolTip: false,
                    ngClick: "showHostSummary($event, inventory.id)",
                    ngClass: "inventory.host_status_class"
                }]
            },
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-md-4 col-sm-3 col-xs-6 List-staticColumnAdjacent',
                modalColumnClass: 'col-md-12',
                awToolTip: "{{ inventory.description | sanitize }}",
                awTipPlacement: "top",
                ngClick: 'editInventory(inventory)'
            },
            kind: {
                label: i18n._('Type'),
                ngBind: 'inventory.kind_label',
                columnClass: 'col-md-2 col-sm-2 hidden-xs'
            },
            organization: {
                label: i18n._('Organization'),
                ngBind: 'inventory.summary_fields.organization.name',
                linkTo: '/#/organizations/{{ inventory.organization }}',
                sourceModel: 'organization',
                sourceField: 'name',
                excludeModal: true,
                columnClass: 'col-md-3 col-sm-2 hidden-xs'
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                type: 'buttonDropdown',
                basePaths: ['inventories'],
                awToolTip: i18n._('Create a new inventory'),
                actionClass: 'btn List-dropdownSuccess',
                buttonContent: '&#43; ' + i18n._('ADD'),
                options: [
                    {
                        optionContent: i18n._('Inventory'),
                        optionSref: 'inventories.add',
                        ngShow: 'canAddInventory'
                    },
                    {
                        optionContent: i18n._('Smart Inventory'),
                        optionSref: 'inventories.addSmartInventory',
                        ngShow: 'canAddInventory'
                    }
                ],
                ngShow: 'canAddInventory'
            }
        },

        fieldActions: {
            columnClass: 'col-md-2 col-sm-3 col-xs-4',
            edit: {
                label: i18n._('Edit'),
                ngClick: 'editInventory(inventory)',
                awToolTip: i18n._('Edit inventory'),
                dataPlacement: 'top',
                ngShow: '!inventory.pending_deletion && inventory.summary_fields.user_capabilities.edit'
            },
            view: {
                label: i18n._('View'),
                ngClick: 'editInventory(inventory)',
                awToolTip: i18n._('View inventory'),
                dataPlacement: 'top',
                ngShow: '!inventory.summary_fields.user_capabilities.edit'
            },
            "delete": {
                label: i18n._('Delete'),
                ngClick: "deleteInventory(inventory.id, inventory.name)",
                awToolTip: i18n._('Delete inventory'),
                dataPlacement: 'top',
                ngShow: '!inventory.pending_deletion && inventory.summary_fields.user_capabilities.delete'

            },
            pending_deletion: {
                label: i18n._('Pending Delete'),
            }
        }
    };}];
