/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default {
    name: 'hosts',
    iterator: 'host',
    editTitle: '{{ selected_group }}',
    showTitle: false,
    well: true,
    wellOverride: true,
    index: false,
    hover: true,
    // hasChildren: true,
    multiSelect: true,
    trackBy: 'host.id',
    basePath:  'api/v2/inventories/{{$stateParams.inventory_id}}/hosts/',

    fields: {
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
            label: 'Hosts',
            ngClick: "editHost(host)",
            ngClass: "{ 'host-disabled-label': !host.enabled }",
            columnClass: 'col-lg-6 col-md-8 col-sm-8 col-xs-7',
            dataHostId: "{{ host.id }}",
            dataType: "host",
            class: 'InventoryManage-breakWord'
        }
    },

    fieldActions: {

        columnClass: 'col-lg-6 col-md-4 col-sm-4 col-xs-5 text-right',
        insights: {
            ngClick: "goToInsights(host)",
            icon: 'fa-info',
            awToolTip: 'View Insights Data',
            dataPlacement: 'top',
            ngShow: 'host.insights_system_id'
        },
        copy: {
            mode: 'all',
            ngClick: "copyMoveHost(host.id)",
            awToolTip: 'Copy or move host to another group',
            dataPlacement: "top",
            ngShow: 'host.summary_fields.user_capabilities.edit'
        },
        edit: {
            //label: 'Edit',
            ngClick: "editHost(host)",
            icon: 'icon-edit',
            awToolTip: 'Edit host',
            dataPlacement: 'top',
            ngShow: 'host.summary_fields.user_capabilities.edit'
        },
        view: {
            //label: 'Edit',
            ngClick: "editHost(host)",
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
        launch: {
            mode: 'all',
            ngDisabled: '!hostsSelected',
            ngClick: 'setAdhocPattern()',
            awToolTip: "Select an inventory source by clicking the check box beside it. The inventory source can be a single host or a selection of multiple hosts.",
            dataPlacement: 'top',
            actionClass: 'btn List-buttonDefault',
            buttonContent: 'RUN COMMANDS',
            showTipWhenDisabled: true,
            tooltipInnerClass: "Tooltip-wide",
            // TODO: we don't always want to show this
            ngShow: true
        },
        system_tracking: {
            buttonContent: 'System Tracking',
            ngClick: 'systemTracking()',
            awToolTip: "Select one or two hosts by clicking the checkbox beside the host. System tracking offers the ability to compare the results of two scan runs from different dates on one host or the same date on two hosts.",
            dataTipWatch: "systemTrackingTooltip",
            dataPlacement: 'top',
            awFeature: 'system_tracking',
            actionClass: 'btn List-buttonDefault system-tracking',
            ngDisabled: 'systemTrackingDisabled || !hostsSelected',
            showTipWhenDisabled: true,
            tooltipInnerClass: "Tooltip-wide",
            ngShow: true
        },
        create: {
            mode: 'all',
            ngClick: "createHost()",
            awToolTip: "Create a new host",
            actionClass: 'btn List-buttonSubmit',
            buttonContent: '&#43; ADD HOST',
            ngShow: 'canAdd',
            dataPlacement: "top",
        }
    }

};
