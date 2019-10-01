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
        layoutClass: 'List-staticColumnLayout--hostsWithCheckbox',
        staticColumns: [
            {
                field: 'toggleHost',
                content: {
                    ngDisabled: '!host.summary_fields.user_capabilities.edit',
                    label: '',
                    type: "toggle",
                    ngClick: "toggleHost($event, host)",
                    awToolTip: "<p>" +
                        i18n._("Indicates if a host is available and should be included in running jobs.") +
                        "</p><p>" +
                        i18n._("For hosts that are part of an external" +
                               " inventory, this may be" +
                               " reset by the inventory sync process.") +
                        "</p>",
                    dataPlacement: "right",
                    nosort: true,
                }
            },
            {
                field: 'active_failures',
                content: {
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
                    columnClass: 'status-column'
                }
            }
        ],

        fields: {
            name: {
                key: true,
                label: i18n._('Hosts'),
                uiSref: ".edit({inventory_id: host.inventory_id,host_id: host.id})",
                ngClass: "{ 'host-disabled-label': !host.enabled }",
                columnClass: 'col-lg-3 col-md-3 col-sm-3 col-xs-7',
                dataHostId: "{{ host.id }}",
                dataType: "host",
            },
            description: {
                label: i18n._('Description'),
                columnClass: 'd-none d-lg-flex col-lg-3',
                template: `
                    <div class="d-inline-block text-truncate">
                        {{ host.description }}
                    </div>
                `
            },
            groups: {
                label: i18n._("Related Groups"),
                type: 'related_groups',
                nosort: true,
                showDelete: true,
                columnClass: 'd-none d-lg-flex List-tableCell col-lg-3'
            }
        },

        fieldActions: {

            columnClass: 'col-lg-3 col-md-6 col-sm-4 col-xs-5 text-right',
            edit: {
                ngClick: "editHost(host)",
                icon: 'icon-edit',
                awToolTip: i18n._('Edit host'),
                dataPlacement: 'top',
                ngShow: 'host.summary_fields.user_capabilities.edit'
            },
            insights: {
                ngClick: "goToInsights(host)",
                icon: 'fa-info',
                awToolTip: i18n._('View Insights Data'),
                dataPlacement: 'top',
                ngShow: 'host.insights_system_id && host.summary_fields.inventory.hasOwnProperty("insights_credential_id")',
                ngClass: "{'List-actionButton--selected': $stateParams['host_id'] == host.id && $state.is('inventories.edit.hosts.edit.insights')}"
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
                actionClass: 'at-Button--add',
                actionId: 'button-add',
                ngShow: 'canAdd',
                dataPlacement: "top",
            }
        }
    };
}];
