/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    angular.module('InventoryHostsDefinition', [])
    .value('InventoryHosts', {

        name: 'hosts',
        iterator: 'host',
        editTitle: '{{ selected_group }}',
        listTitle: 'Hosts',
        searchSize: 'col-lg-12 col-md-12 col-sm-12 col-xs-12',
        showTitle: false,
        well: true,
        index: false,
        hover: true,
        hasChildren: true,
        'class': 'table-no-border',
        multiSelect: true,

        fields: {
            active_failures: {
                label: '',
                iconOnly: true,
                searchable: false,
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
                searchLabel: 'Name',
                ngClick: "editHost(host.id)",
                ngClass: "{ 'host-disabled-label': !host.enabled }",
                columnClass: 'col-lg-6 col-md-8 col-sm-8 col-xs-7',
                dataHostId: "{{ host.id }}",
                dataType: "host",
                class: 'InventoryManage-breakWord'
            },
            enabled: {
                label: 'Disabled?',
                searchSingleValue: true,
                searchType: 'boolean',
                typeOptions: [
                    {label: "Yes", value: false},
                    {label: "No", value: true}
                ],
                searchValue: 'false',
                searchOnly: true
            },
            has_active_failures: {
                label: 'Failed jobs?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
            }
        },

        fieldActions: {

            columnClass: 'col-lg-6 col-md-4 col-sm-4 col-xs-5 text-right',
            copy: {
                mode: 'all',
                ngClick: "copyMoveHost(host.id)",
                awToolTip: 'Copy or move host to another group',
                dataPlacement: "top"
            },
            edit: {
                //label: 'Edit',
                ngClick: "editHost(host.id)",
                icon: 'icon-edit',
                awToolTip: 'Edit host',
                dataPlacement: 'top'
            },
            "delete": {
                //label: 'Delete',
                ngClick: "deleteHost(host.id, host.name)",
                icon: 'icon-trash',
                awToolTip: 'Delete host',
                dataPlacement: 'top'
            }
        },

        actions: {
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
                tooltipInnerClass: "Tooltip-wide"
            },
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refreshGroups()",
                ngShow: "socketStatus == 'error'",
                actionClass: 'btn List-buttonDefault',
                buttonContent: 'REFRESH'
            },
            create: {
                mode: 'all',
                ngClick: "createHost()",
                awToolTip: "Create a new host",
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ADD HOST'
            }
        }

    });
