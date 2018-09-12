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
        disableRowValue: 'inventory.pending_deletion',
        layoutClass: 'List-staticColumnLayout--toggleOnOff',
        staticColumns: [
            {
                field: 'status',
                content: {
                    label: '',
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
                        ngClick: "showHostSummary($event, inventory.id)"
                    }]
                }
            }
        ],

        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-md-4 col-sm-4 col-xs-8',
                modalColumnClass: 'col-md-12',
                awToolTip: "{{ inventory.description | sanitize }}",
                awTipPlacement: "top",
                uiSref: '{{inventory.linkToDetails}}'
            },
            kind: {
                label: i18n._('Type'),
                ngBind: 'inventory.kind_label',
                columnClass: 'd-none d-sm-flex col-sm-2'
            },
            organization: {
                label: i18n._('Organization'),
                ngBind: 'inventory.summary_fields.organization.name',
                linkTo: '/#/organizations/{{ inventory.organization }}',
                sourceModel: 'organization',
                sourceField: 'name',
                excludeModal: true,
                columnClass: 'd-none d-sm-flex col-md-3 col-sm-2'
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                type: 'buttonDropdown',
                basePaths: ['inventories'],
                awToolTip: i18n._('Create a new inventory'),
                actionClass: 'at-Button--add',
                actionId: 'button-add',
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
            columnClass: 'col-md-3 col-sm-4 col-xs-4',
            edit: {
                label: i18n._('Edit'),
                ngClick: 'editInventory(inventory)',
                awToolTip: i18n._('Edit inventory'),
                dataPlacement: 'top',
                ngShow: '!inventory.pending_deletion && inventory.summary_fields.user_capabilities.edit'
            },
            copy: {
                label: i18n._('Copy'),
                ngClick: 'copyInventory(inventory)',
                awToolTip: "{{ inventory.copyTip }}",
                dataTipWatch: "inventory.copyTip",
                dataPlacement: 'top',
                ngShow: '!inventory.pending_deletion && inventory.summary_fields.user_capabilities.copy',
                ngClass: 'inventory.copyClass'
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
