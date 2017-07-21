/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {
        name: 'hosts',
        iterator: 'host',
        editTitle: '{{ selected_group }}',
        singleSearchParam: {
            param: 'host_filter'
        },
        showTitle: false,
        well: true,
        index: false,
        hover: true,
        hasChildren: true,
        'class': 'table-no-border',
        trackBy: 'host.id',
        basePath: 'hosts',
        title: false,
        actionHolderClass: 'List-actionHolder List-actionHolder--leftAlign',

        fields: {
            toggleHost: {
                ngDisabled: 'host.has_inventory_sources',
                label: '',
                columnClass: 'List-staticColumn--toggle',
                type: "toggle",
                ngClick: "toggleHost($event, host)",
                awToolTip: "<p>" +
                    i18n._("Indicates if a host is available and should be included in running jobs.") +
                    "</p><p>" +
                    i18n._("For hosts that are part of an external" +
                           " inventory, this flag cannot be changed. It will be" +
                           " set by the inventory sync process.") +
                    "</p>",
                dataPlacement: "right",
                nosort: true,
            },
            active_failures: {
                label: '',
                iconOnly: true,
                nosort: true,
                // do not remove this ng-click directive
                // the list generator case to handle fields without ng-click
                // cannot handle the aw-* directives
                ngClick: 'noop()',
                awPopOver: "{{ host.job_status_html }}",
                dataTitle: "{{ host.job_status_title }}",
                awToolTip: "{{ host.badgeToolTip }}",
                dataPlacement: 'top',
                icon: "{{ 'fa icon-job-' + host.active_failures }}",
                id: 'active-failures-action',
                columnClass: 'status-column List-staticColumn--smallStatus'
            },
            name: {
                key: true,
                label: i18n._('Name'),
                ngClick: "editHost(host.id)",
                columnClass: 'col-lg-6 col-md-8 col-sm-8 col-xs-7',
                dataHostId: "{{ host.id }}",
                dataType: "host",
                class: 'InventoryManage-breakWord'
            },
            inventory: {
                label: i18n._('Inventory'),
                sourceModel: 'inventory',
                sourceField: 'name',
                columnClass: 'col-lg-5 col-md-4 col-sm-4 hidden-xs elllipsis',
                ngClick: "editInventory(host)"
            }
        },

        fieldActions: {

            columnClass: 'col-lg-6 col-md-4 col-sm-4 col-xs-5 text-right',
            edit: {
                ngClick: "editHost(host.id)",
                icon: 'icon-edit',
                awToolTip: i18n._('Edit host'),
                dataPlacement: 'top',
                ngShow: 'host.summary_fields.user_capabilities.edit'
            },
            view: {
                ngClick: "editHost(host.id)",
                awToolTip: i18n._('View host'),
                dataPlacement: 'top',
                ngShow: '!host.summary_fields.user_capabilities.edit'
            }
        },

        actions: {
            refresh: {
                mode: 'all',
                awToolTip: i18n._("Refresh the page"),
                ngClick: "refreshGroups()",
                ngShow: "socketStatus == 'error'",
                actionClass: 'btn List-buttonDefault',
                buttonContent: i18n._('REFRESH')
            },
            smart_inventory: {
                mode: 'all',
                ngClick: "smartInventory()",
                awToolTip: i18n._("Create a new Smart Inventory from search results."),
                actionClass: 'btn List-buttonDefault',
                buttonContent: i18n._('SMART INVENTORY'),
                ngShow: 'canAdd && (hosts.length > 0 || !(searchTags | isEmpty))',
                dataPlacement: "top",
                ngDisabled: '!enableSmartInventoryButton'
            }
        }
    };
}];
