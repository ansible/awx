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
        searchSize: 'col-lg-12 col-md-12 col-sm-12 col-xs-12',
        showTitle: false,
        well: true,
        index: false,
        hover: true,
        hasChildren: true,
        'class': 'table-no-border',
        trackBy: 'host.id',
        title: false,

        fields: {
            toggleHost: {
                ngDisabled: "!host.summary_fields.user_capabilities.edit",
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
                label: 'Name',
                ngClick: "editHost(host.id)",
                columnClass: 'col-lg-6 col-md-8 col-sm-8 col-xs-7',
                dataHostId: "{{ host.id }}",
                dataType: "host",
                class: 'InventoryManage-breakWord'
            }
        },

        fieldActions: {

            columnClass: 'col-lg-6 col-md-4 col-sm-4 col-xs-5 text-right',
            copy: {
                mode: 'all',
                ngClick: "copyMoveHost(host.id)",
                awToolTip: 'Copy or move host to another group',
                dataPlacement: "top",
                ngShow: 'host.summary_fields.user_capabilities.edit'
            },
            edit: {
                //label: 'Edit',
                ngClick: "editHost(host.id)",
                icon: 'icon-edit',
                awToolTip: 'Edit host',
                dataPlacement: 'top',
                ngShow: 'host.summary_fields.user_capabilities.edit'
            },
            view: {
                //label: 'Edit',
                ngClick: "editHost(host.id)",
                awToolTip: 'View host',
                dataPlacement: 'top',
                ngShow: '!host.summary_fields.user_capabilities.edit'
            },
            "delete": {
                //label: 'Delete',
                ngClick: "deleteHost(host.id, host.name)",
                icon: 'icon-trash',
                awToolTip: 'Delete host',
                dataPlacement: 'top',
                ngShow: 'host.summary_fields.user_capabilities.delete'
            }
        },

        actions: {
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refreshGroups()",
                ngShow: "socketStatus == 'error'",
                actionClass: 'btn List-buttonDefault',
                buttonContent: 'REFRESH'
            },
            smart_inventory: {
                mode: 'all',
                ngClick: "smartInventory()",
                awToolTip: "Create a new Smart Inventory from results.",
                actionClass: 'btn List-buttonDefault',
                buttonContent: 'SMART INVENTORY',
                ngShow: 'canAdd',
                dataPlacement: "top",
            }
        }
    };
}];
