/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    angular.module('InventoryGroupsDefinition', [])
    .value('InventoryGroups', {

        name: 'groups',
        iterator: 'group',
        editTitle: '{{ inventory.name }}',
        listTitle: 'Groups',
        searchSize: 'col-lg-12 col-md-12 col-sm-12 col-xs-12',
        showTitle: false,
        well: true,
        index: false,
        hover: true,
        'class': 'table-no-border',
        multiSelect: true,
        trackBy: 'group.id',

        fields: {
            sync_status: {
                label: '',
                nosort: true,
                mode: 'all',
                iconOnly: true,
                ngClick: 'viewUpdateStatus(group.id)',
                awToolTip: "{{ group.status_tooltip }}",
                dataTipWatch: "group.status_tooltip",
                icon: "{{ 'fa icon-cloud-' + group.status_class }}",
                ngClass: "group.status_class",
                dataPlacement: "top",
                columnClass: 'status-column List-staticColumn--smallStatus'
            },
            failed_hosts: {
                label: '',
                nosort: true,
                mode: 'all',
                iconOnly: true,
                awToolTip: "{{ group.hosts_status_tip }}",
                dataPlacement: "top",
                ngClick: "showFailedHosts(group)",
                icon: "{{ 'fa icon-job-' + group.hosts_status_class }}",
                columnClass: 'status-column List-staticColumn--smallStatus'
            },
            name: {
                label: 'Groups',
                key: true,
                ngClick: "groupSelect(group.id)",
                columnClass: 'col-lg-3 col-md-3 col-sm-3 col-xs-3',
                class: 'InventoryManage-breakWord',
            },
            total_groups: {
                nosort: true,
                label: '',
                type: 'badgeCount',
                ngHide: 'group.total_groups == 0',
                noLink: true,
                awToolTip: "{{group.name | sanitize}} contains {{group.total_groups}} {{group.total_groups === 1 ? 'child' : 'children'}}"
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
            launch: {
                mode: 'all',
                // $scope.$parent is governed by InventoryManageController,
                ngDisabled: '!$parent.groupsSelected && !$parent.hostsSelected',
                ngClick: '$parent.setAdhocPattern()',
                awToolTip: "Select an inventory source by clicking the check box beside it. The inventory source can be a single group or host, a selection of multiple hosts, or a selection of multiple groups.",
                dataTipWatch: "adhocCommandTooltip",
                actionClass: 'btn List-buttonDefault',
                buttonContent: 'RUN COMMANDS',
                showTipWhenDisabled: true,
                tooltipInnerClass: "Tooltip-wide",
                ngShow: 'canAdhoc'
                // TODO: set up a tip watcher and change text based on when
                // things are selected/not selected.  This is started and
                // commented out in the inventory controller within the watchers.
                // awToolTip: "{{ adhocButtonTipContents }}",
                // dataTipWatch: "adhocButtonTipContents"
            },
            create: {
                mode: 'all',
                ngClick: "createGroup()",
                awToolTip: "Create a new group",
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ADD GROUP',
                ngShow: 'canAdd'
            }
        },

        fieldActions: {

            columnClass: 'col-lg-6 col-md-6 col-sm-6 col-xs-6 text-right',

            group_update: {
                //label: 'Sync',
                mode: 'all',
                ngClick: 'updateGroup(group)',
                awToolTip: "{{ group.launch_tooltip }}",
                dataTipWatch: "group.launch_tooltip",
                ngShow: "(group.status !== 'running' && group.status " +
                    "!== 'pending' && group.status !== 'updating') && group.summary_fields.user_capabilities.start",
                ngClass: "group.launch_class",
                dataPlacement: "top",
            },
            cancel: {
                //label: 'Cancel',
                mode: 'all',
                ngClick: "cancelUpdate(group.id)",
                awToolTip: "Cancel sync process",
                'class': 'red-txt',
                ngShow: "(group.status == 'running' || group.status == 'pending' " +
                    "|| group.status == 'updating') && group.summary_fields.user_capabilities.start",
                dataPlacement: "top",
                iconClass: "fa fa-minus-circle"
            },
            copy: {
                mode: 'all',
                ngClick: "copyMoveGroup(group.id)",
                awToolTip: 'Copy or move group',
                ngShow: "group.id > 0 && group.summary_fields.user_capabilities.copy",
                dataPlacement: "top"
            },
            schedule: {
                mode: 'all',
                ngClick: "scheduleGroup(group.id)",
                awToolTip: "{{ group.group_schedule_tooltip }}",
                ngClass: "group.scm_type_class",
                dataPlacement: 'top',
                ngShow: "!(group.summary_fields.inventory_source.source === '') && group.summary_fields.user_capabilities.schedule"
            },
            edit: {
                //label: 'Edit',
                mode: 'all',
                ngClick: "editGroup(group.id)",
                awToolTip: 'Edit group',
                dataPlacement: "top",
                ngShow: "group.summary_fields.user_capabilities.edit"
            },
            view: {
                //label: 'Edit',
                mode: 'all',
                ngClick: "editGroup(group.id)",
                awToolTip: 'View group',
                dataPlacement: "top",
                ngShow: "!group.summary_fields.user_capabilities.edit"
            },
            "delete": {
                //label: 'Delete',
                mode: 'all',
                ngClick: "deleteGroup(group)",
                awToolTip: 'Delete group',
                dataPlacement: "top",
                ngShow: "group.summary_fields.user_capabilities.delete"
            }
        }
    });
