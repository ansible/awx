/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {
        name: 'nested_hosts',
        iterator: 'nested_host',
        editTitle: '{{ nested_host.name }}', // i don't think this is correct
        // showTitle: false,
        well: true,
        wellOverride: true,
        index: false,
        hover: true,
        // hasChildren: true,
        multiSelect: true,
        trackBy: 'nested_host.id',
        basePath:  'api/v2/groups/{{$stateParams.group_id}}/all_hosts/',
        layoutClass: 'List-staticColumnLayout--hostsWithCheckbox',
        staticColumns: [
            {
                field: 'toggleHost',
                content: {
                    ngDisabled: '!nested_host.summary_fields.user_capabilities.edit',
                    label: '',
                    columnClass: 'List-staticColumn--toggle',
                    type: "toggle",
                    ngClick: "toggleHost($event, nested_host)",
                    awToolTip: "<p>" +
                        i18n._("Indicates if a host is available and should be included in running jobs.") +
                        "</p><p>" +
                        i18n._("For hosts that are part of an external" +
                               " inventory, this flag may be" +
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
                    awPopOver: "{{ nested_host.job_status_html }}",
                    dataTitle: "{{ nested_host.job_status_title }}",
                    awToolTip: "{{ nested_host.badgeToolTip }}",
                    dataPlacement: 'top',
                    icon: "{{ 'fa icon-job-' + nested_host.active_failures }}",
                    id: 'active-failures-action',
                    columnClass: 'status-column List-staticColumn--smallStatus'
                }
            }
        ],

        fields: {
            name: {
                key: true,
                label: i18n._('Hosts'),
                uiSref: "inventories.edit.hosts.edit({host_id: nested_host.id})",
                ngClass: "{ 'host-disabled-label': !nested_host.enabled }",
                columnClass: 'col-lg-4 col-md-8 col-sm-8 col-xs-7',
                dataHostId: "{{ nested_host.id }}",
                dataType: "nested_host",
            },
            description: {
                label: i18n._('Description'),
                columnClass: 'd-none d-lg-flex col-lg-4',
                template: `
                    <div class="d-inline-block text-truncate">
                        {{ nested_host.description }}
                    </div>
                `
            },
        },

        fieldActions: {

            columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-5 text-right',
            edit: {
                ngClick: "editHost(nested_host.id)",
                icon: 'icon-edit',
                awToolTip: i18n._('Edit host'),
                dataPlacement: 'top',
                ngShow: 'nested_host.summary_fields.user_capabilities.edit'
            },
            view: {
                ngClick: "editHost(nested_host.id)",
                awToolTip: i18n._('View host'),
                dataPlacement: 'top',
                ngShow: '!nested_host.summary_fields.user_capabilities.edit'
            },
            "delete": {
                //label: 'Delete',
                ngClick: "disassociateHost(nested_host)",
                iconClass: 'fa fa-times',
                awToolTip: i18n._('Disassociate host'),
                dataPlacement: 'top',
                ngShow: 'nested_host.summary_fields.user_capabilities.delete'
            }
        },

        actions: {
            launch: {
                mode: 'all',
                ngDisabled: '!hostsSelected',
                ngClick: 'setAdhocPattern()',
                awToolTip: i18n._("Select an inventory source by clicking the check box beside it. The inventory source can be a single group or host, a selection of multiple hosts, or a selection of multiple groups."),
                dataPlacement: 'top',
                actionClass: 'btn List-buttonDefault',
                buttonContent: i18n._('RUN COMMANDS'),
                showTipWhenDisabled: true,
                tooltipInnerClass: "Tooltip-wide",
                // TODO: we don't always want to show this
                ngShow: 'inventory_obj.summary_fields.user_capabilities.adhoc'
            },
            refresh: {
                mode: 'all',
                awToolTip: i18n._("Refresh the page"),
                ngClick: "refreshGroups()",
                ngShow: "socketStatus == 'error'",
                actionClass: 'btn List-buttonDefault',
                buttonContent: i18n._('REFRESH')
            },
            add: {
                mode: 'all',
                type: 'buttonDropdown',
                awToolTip: i18n._("Add a host"),
                actionClass: 'at-Button--add',
                actionId: 'button-add',
                ngShow: 'canAdd',
                dataPlacement: "top",
                options: [
                    {
                        optionContent: i18n._('Existing Host'),
                        optionSref: '.associate',
                        ngShow: 'canAdd'
                    },
                    {
                        optionContent: i18n._('New Host'),
                        optionSref: '.add',
                        ngShow: 'canAdd'
                    }
                ],
            }
        }
    };
}];
