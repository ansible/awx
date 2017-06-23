/*************************************************
 * Copyright (c) 2017  Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default {
    name: 'nested_groups',
    iterator: 'nested_group',
    editTitle: '{{ inventory.name }}',
    well: true,
    wellOverride: true,
    index: false,
    hover: true,
    multiSelect: true,
    trackBy: 'nested_group.id',
    basePath:  'api/v2/inventories/{{$stateParams.inventory_id}}/root_groups/',

    fields: {
        failed_hosts: {
            label: '',
            nosort: true,
            mode: 'all',
            iconOnly: true,
            awToolTip: "{{ nested_group.hosts_status_tip }}",
            dataPlacement: "top",
            icon: "{{ 'fa icon-job-' + nested_group.hosts_status_class }}",
            columnClass: 'status-column List-staticColumn--smallStatus'
        },
        name: {
            label: 'Groups',
            key: true,

            // ngClick: "groupSelect(group.id)",
            ngClick: "editGroup(nested_group.id)",
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
            awToolTip: "Select an inventory source by clicking the check box beside it. The inventory source can be a single group or host, a selection of multiple hosts, or a selection of multiple groups.",
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
        add: {
            mode: 'all',
            type: 'buttonDropdown',
            awToolTip: "Add a group",
            actionClass: 'btn List-buttonSubmit',
            buttonContent: '&#43; ADD',
            ngShow: 'canAdd',
            dataPlacement: "top",
            options: [
                {
                    optionContent: 'Existing Group',
                    optionSref: '.associate',
                    ngShow: 'canAdd'
                },
                {
                    optionContent: 'New Group',
                    optionSref: '.add',
                    ngShow: 'canAdd'
                }
            ],
        }
    },

    fieldActions: {

        columnClass: 'col-lg-6 col-md-6 col-sm-6 col-xs-6 text-right',

        edit: {
            //label: 'Edit',
            mode: 'all',
            ngClick: "editGroup(nested_group.id)",
            awToolTip: 'Edit group',
            dataPlacement: "top",
            ngShow: "nested_group.summary_fields.user_capabilities.edit"
        },
        view: {
            //label: 'Edit',
            mode: 'all',
            ngClick: "editGroup(nested_group.id)",
            awToolTip: 'View group',
            dataPlacement: "top",
            ngShow: "!nested_group.summary_fields.user_capabilities.edit"
        },
        "delete": {
            //label: 'Delete',
            mode: 'all',
            ngClick: "disassociateGroup(nested_group)",
            awToolTip: 'Delete group',
            dataPlacement: "top",
            ngShow: "nested_group.summary_fields.user_capabilities.delete"
        }
    }
};
