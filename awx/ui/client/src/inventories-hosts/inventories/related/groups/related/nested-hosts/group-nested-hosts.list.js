/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import { N_ } from '../../../../../../i18n';

export default {
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

    fields: {
        toggleHost: {
            ngDisabled: 'host.has_inventory_sources',
            label: '',
            columnClass: 'List-staticColumn--toggle',
            type: "toggle",
            ngClick: "toggleHost($event, nested_host)",
            awToolTip: "<p>" +
                N_("Indicates if a host is available and should be included in running jobs.") +
                "</p><p>" +
                N_("For hosts that are part of an external" +
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
            awPopOver: "{{ nested_host.job_status_html }}",
            dataTitle: "{{ nested_host.job_status_title }}",
            awToolTip: "{{ nested_host.badgeToolTip }}",
            dataPlacement: 'top',
            icon: "{{ 'fa icon-job-' + nested_host.active_failures }}",
            id: 'active-failures-action',
            columnClass: 'status-column List-staticColumn--smallStatus'
        },
        name: {
            key: true,
            label: N_('Hosts'),
            ngClick: "editHost(nested_host.id)",
            ngClass: "{ 'host-disabled-label': !nested_host.enabled }",
            columnClass: 'col-lg-6 col-md-8 col-sm-8 col-xs-7',
            dataHostId: "{{ nested_host.id }}",
            dataType: "nested_host",
            class: 'InventoryManage-breakWord'
        }
    },

    fieldActions: {

        columnClass: 'col-lg-6 col-md-4 col-sm-4 col-xs-5 text-right',
        edit: {
            ngClick: "editHost(nested_host.id)",
            icon: 'icon-edit',
            awToolTip: N_('Edit host'),
            dataPlacement: 'top',
            ngShow: 'nested_host.summary_fields.user_capabilities.edit'
        },
        view: {
            ngClick: "editHost(nested_host.id)",
            awToolTip: N_('View host'),
            dataPlacement: 'top',
            ngShow: '!nested_host.summary_fields.user_capabilities.edit'
        },
        "delete": {
            //label: 'Delete',
            ngClick: "disassociateHost(nested_host)",
            icon: 'icon-trash',
            awToolTip: N_('Disassociate host'),
            dataPlacement: 'top',
            ngShow: 'nested_host.summary_fields.user_capabilities.delete'
        }
    },

    actions: {
        launch: {
            mode: 'all',
            ngDisabled: '!hostsSelected',
            ngClick: 'setAdhocPattern()',
            awToolTip: N_("Select an inventory source by clicking the check box beside it. The inventory source can be a single group or host, a selection of multiple hosts, or a selection of multiple groups."),
            dataPlacement: 'top',
            actionClass: 'btn List-buttonDefault',
            buttonContent: N_('RUN COMMANDS'),
            showTipWhenDisabled: true,
            tooltipInnerClass: "Tooltip-wide",
            // TODO: we don't always want to show this
            ngShow: true
        },
        system_tracking: {
            buttonContent: N_('System Tracking'),
            ngClick: 'systemTracking()',
            awToolTip: N_("Select one or two hosts by clicking the checkbox beside the host. System tracking offers the ability to compare the results of two scan runs from different dates on one host or the same date on two hosts."),
            dataTipWatch: "systemTrackingTooltip",
            dataPlacement: 'top',
            awFeature: 'system_tracking',
            actionClass: 'btn List-buttonDefault system-tracking',
            ngDisabled: 'systemTrackingDisabled || !hostsSelected',
            showTipWhenDisabled: true,
            tooltipInnerClass: "Tooltip-wide",
            ngShow: true
        },
        refresh: {
            mode: 'all',
            awToolTip: N_("Refresh the page"),
            ngClick: "refreshGroups()",
            ngShow: "socketStatus == 'error'",
            actionClass: 'btn List-buttonDefault',
            buttonContent: N_('REFRESH')
        },
        add: {
            mode: 'all',
            type: 'buttonDropdown',
            awToolTip: N_("Add a host"),
            actionClass: 'btn List-buttonSubmit',
            buttonContent: '&#43; ' + N_('ADD'),
            ngShow: 'canAdd',
            dataPlacement: "top",
            options: [
                {
                    optionContent: N_('Existing Host'),
                    optionSref: '.associate',
                    ngShow: 'canAdd'
                },
                {
                    optionContent: N_('New Host'),
                    optionSref: '.add',
                    ngShow: 'canAdd'
                }
            ],
        }
    }

};
