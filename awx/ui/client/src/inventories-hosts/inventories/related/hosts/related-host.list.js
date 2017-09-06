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
        showTitle: false,
        well: true,
        wellOverride: true,
        index: false,
        hover: true,
        multiSelect: true,
        trackBy: 'host.id',
        basePath:  'api/v2/inventories/{{$stateParams.inventory_id}}/hosts/',

        fields: {
            toggleHost: {
                ngDisabled: '!host.summary_fields.user_capabilities.edit || host.has_inventory_sources',
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
                label: i18n._('Hosts'),
                ngClick: "editHost(host)",
                ngClass: "{ 'host-disabled-label': !host.enabled }",
                columnClass: 'col-lg-6 col-md-8 col-sm-8 col-xs-7',
                dataHostId: "{{ host.id }}",
                dataType: "host",
                class: 'InventoryManage-breakWord'
            },
            groups: {
                label: i18n._("Related Groups"),
                type: 'related_groups',
                nosort: true,
                showDelete: true,
                columnClass: 'RelatedGroupsLabelsCell List-tableCell col-lg-2 col-md-3 hidden-sm hidden-xs'
            }
        },

        fieldActions: {

            columnClass: 'col-lg-6 col-md-4 col-sm-4 col-xs-5 text-right',
            insights: {
                ngClick: "goToInsights(host)",
                icon: 'fa-info',
                awToolTip: i18n._('View Insights Data'),
                dataPlacement: 'top',
                ngShow: 'host.insights_system_id && host.summary_fields.inventory.hasOwnProperty("insights_credential_id")',
                ngClass: "{'List-actionButton--selected': $stateParams['host_id'] == host.id && $state.is('inventories.edit.hosts.edit.insights')}"
            },
            edit: {
                ngClick: "editHost(host)",
                icon: 'icon-edit',
                awToolTip: i18n._('Edit host'),
                dataPlacement: 'top',
                ngShow: 'host.summary_fields.user_capabilities.edit'
            },
            view: {
                ngClick: "editHost(host)",
                awToolTip: i18n._('View host'),
                dataPlacement: 'top',
                ngShow: '!host.summary_fields.user_capabilities.edit'
            },
            "delete": {
                ngClick: "deleteHost(host.id, host.name)",
                icon: 'icon-trash',
                awToolTip: i18n._('Delete host'),
                dataPlacement: 'top',
                ngShow: 'host.summary_fields.user_capabilities.delete'
            }
        },

        actions: {
            launch: {
                mode: 'all',
                ngDisabled: '!hostsSelected',
                ngClick: 'setAdhocPattern()',
                awToolTip: i18n._("Select an inventory source by clicking the check box beside it. The inventory source can be a single host or a selection of multiple hosts."),
                dataPlacement: 'top',
                actionClass: 'btn List-buttonDefault',
                buttonContent: i18n._('RUN COMMANDS'),
                showTipWhenDisabled: true,
                tooltipInnerClass: "Tooltip-wide",
                // TODO: we don't always want to show this
                ngShow: 'inventory_obj.summary_fields.user_capabilities.adhoc'
            },
            create: {
                mode: 'all',
                ngClick: "createHost()",
                awToolTip: i18n._("Create a new host"),
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ' + i18n._('ADD HOST'),
                ngShow: 'canAdd',
                dataPlacement: "top",
            }
        }
    };
}];
