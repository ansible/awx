/*************************************************
 * Copyright (c) 2017  Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default {
    name: 'inventory_sources',
    iterator: 'inventory_source',
    editTitle: '{{ inventory_source.name }}',
    well: true,
    wellOverride: true,
    index: false,
    hover: true,
    multiSelect: true,
    trackBy: 'inventory_source.id',
    basePath:  'api/v2/inventories/{{$stateParams.inventory_id}}/inventory_sources/',

    fields: {
        sync_status: {
            label: '',
            nosort: true,
            mode: 'all',
            iconOnly: true,
            ngClick: 'viewUpdateStatus(inventory_source.id)',
            awToolTip: "{{ inventory_source.status_tooltip }}",
            dataTipWatch: "inventory_source.status_tooltip",
            icon: "{{ 'fa icon-cloud-' + inventory_source.status_class }}",
            ngClass: "inventory_source.status_class",
            dataPlacement: "top",
            columnClass: 'status-column List-staticColumn--smallStatus'
        },
        name: {
            label: 'Sources',
            key: true,
            ngClick: "groupSelect(inventory_source.id)",
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
        // launch: {
        //     mode: 'all',
        //     // $scope.$parent is governed by InventoryManageController,
        //     ngDisabled: '!$parent.groupsSelected && !$parent.hostsSelected',
        //     ngClick: '$parent.setAdhocPattern()',
        //     awToolTip: "Select an inventory source by clicking the check box beside it. The inventory source can be a single group or host, a selection of multiple hosts, or a selection of multiple groups.",
        //     dataTipWatch: "adhocCommandTooltip",
        //     actionClass: 'btn List-buttonDefault',
        //     buttonContent: 'RUN COMMANDS',
        //     showTipWhenDisabled: true,
        //     tooltipInnerClass: "Tooltip-wide",
        //     ngShow: 'canAdhoc'
        //     // TODO: set up a tip watcher and change text based on when
        //     // things are selected/not selected.  This is started and
        //     // commented out in the inventory controller within the watchers.
        //     // awToolTip: "{{ adhocButtonTipContents }}",
        //     // dataTipWatch: "adhocButtonTipContents"
        // },
        create: {
            mode: 'all',
            ngClick: "createSource()",
            awToolTip: "Create a new source",
            actionClass: 'btn List-buttonSubmit',
            buttonContent: '&#43; ADD SOURCE',
            ngShow: 'canAdd',
            dataPlacement: "top",
        }
    },

    fieldActions: {

        columnClass: 'col-lg-6 col-md-6 col-sm-6 col-xs-6 text-right',

        group_update: {
            //label: 'Sync',
            mode: 'all',
            ngClick: 'updateSource(inventory_source)',
            awToolTip: "{{ inventory_source.launch_tooltip }}",
            dataTipWatch: "inventory_source.launch_tooltip",
            ngShow: "(inventory_source.status !== 'running' && inventory_source.status " +
                "!== 'pending' && inventory_source.status !== 'updating') && inventory_source.summary_fields.user_capabilities.start",
            ngClass: "inventory_source.launch_class",
            dataPlacement: "top",
        },
        cancel: {
            //label: 'Cancel',
            mode: 'all',
            ngClick: "cancelUpdate(inventory_source.id)",
            awToolTip: "Cancel sync process",
            'class': 'red-txt',
            ngShow: "(inventory_source.status == 'running' || inventory_source.status == 'pending' " +
                "|| inventory_source.status == 'updating') && inventory_source.summary_fields.user_capabilities.start",
            dataPlacement: "top",
            iconClass: "fa fa-minus-circle"
        },
        copy: {
            mode: 'all',
            ngClick: "copyMoveSource(inventory_source.id)",
            awToolTip: 'Copy or move source',
            ngShow: "inventory_source.id > 0 && inventory_source.summary_fields.user_capabilities.copy",
            dataPlacement: "top"
        },
        schedule: {
            mode: 'all',
            ngClick: "scheduleSource(inventory_source.id)",
            awToolTip: "{{ inventory_source.group_schedule_tooltip }}",
            ngClass: "inventory_source.scm_type_class",
            dataPlacement: 'top',
            ngShow: "!(inventory_source.summary_fields.inventory_source.source === '')"
        },
        edit: {
            //label: 'Edit',
            mode: 'all',
            ngClick: "editSource(inventory_source.id)",
            awToolTip: 'Edit source',
            dataPlacement: "top",
            ngShow: "inventory_source.summary_fields.user_capabilities.edit"
        },
        view: {
            //label: 'Edit',
            mode: 'all',
            ngClick: "editSource(inventory_source.id)",
            awToolTip: 'View source',
            dataPlacement: "top",
            ngShow: "!inventory_source.summary_fields.user_capabilities.edit"
        },
        "delete": {
            //label: 'Delete',
            mode: 'all',
            ngClick: "deleteSource(inventory_source)",
            awToolTip: 'Delete source',
            dataPlacement: "top",
            ngShow: "inventory_source.summary_fields.user_capabilities.delete"
        }
    }
};
