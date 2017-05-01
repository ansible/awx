/*************************************************
 * Copyright (c) 2017  Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default {
    name: 'groups',
    iterator: 'group',
    editTitle: '{{ inventory.name }}',
    well: true,
    wellOverride: true,
    index: false,
    hover: true,
    multiSelect: true,
    trackBy: 'group.id',
    basePath:  'api/v2/inventories/{{$stateParams.inventory_id}}/root_groups/',

    fields: {
        failed_hosts: {
            label: '',
            nosort: true,
            mode: 'all',
            iconOnly: true,
            awToolTip: "{{ group.hosts_status_tip }}",
            dataPlacement: "top",
            icon: "{{ 'fa icon-job-' + group.hosts_status_class }}",
            columnClass: 'status-column List-staticColumn--smallStatus'
        },
        name: {
            label: 'Groups',
            key: true,
            ngClick: "editGroup(group.id)",
            columnClass: 'col-lg-6 col-md-6 col-sm-6 col-xs-6',
            class: 'InventoryManage-breakWord',
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
            ngDisabled: '!groupsSelected',
            ngClick: 'setAdhocPattern()',
            awToolTip: "Select an inventory source by clicking the check box beside it. The inventory source can be a single group or a selection of multiple groups.",
            dataPlacement: 'top',
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
            ngShow: 'canAdd',
            dataPlacement: "top",
        }
    },

    fieldActions: {

        columnClass: 'col-lg-6 col-md-6 col-sm-6 col-xs-6 text-right',

        // group_update: {
        //     //label: 'Sync',
        //     mode: 'all',
        //     ngClick: 'updateGroup(group)',
        //     awToolTip: "{{ group.launch_tooltip }}",
        //     dataTipWatch: "group.launch_tooltip",
        //     ngShow: "(group.status !== 'running' && group.status " +
        //         "!== 'pending' && group.status !== 'updating') && group.summary_fields.user_capabilities.start",
        //     ngClass: "group.launch_class",
        //     dataPlacement: "top",
        // },
        // cancel: {
        //     //label: 'Cancel',
        //     mode: 'all',
        //     ngClick: "cancelUpdate(group.id)",
        //     awToolTip: "Cancel sync process",
        //     'class': 'red-txt',
        //     ngShow: "(group.status == 'running' || group.status == 'pending' " +
        //         "|| group.status == 'updating') && group.summary_fields.user_capabilities.start",
        //     dataPlacement: "top",
        //     iconClass: "fa fa-minus-circle"
        // },
        copy: {
            mode: 'all',
            ngClick: "copyMoveGroup(group.id)",
            awToolTip: 'Copy or move group',
            ngShow: "group.id > 0 && group.summary_fields.user_capabilities.copy",
            dataPlacement: "top"
        },
        // schedule: {
        //     mode: 'all',
        //     ngClick: "scheduleGroup(group.id)",
        //     awToolTip: "{{ group.group_schedule_tooltip }}",
        //     ngClass: "group.scm_type_class",
        //     dataPlacement: 'top',
        //     ngShow: "!(group.summary_fields.inventory_source.source === '')"
        // },
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
};
