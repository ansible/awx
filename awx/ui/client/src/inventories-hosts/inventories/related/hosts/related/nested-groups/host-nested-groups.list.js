/*************************************************
 * Copyright (c) 2017  Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default ['i18n', function(i18n) {
     return {
        name: 'nested_groups',
        iterator: 'nested_group',
        editTitle: '{{ inventory.name }}',
        well: true,
        wellOverride: true,
        index: false,
        hover: true,
        multiSelect: true,
        trackBy: 'nested_group.id',
        basePath: 'api/v2/hosts/{{$stateParams.host_id}}/all_groups/',
        layoutClass: 'List-staticColumnLayout--groups',
        staticColumns: [
            {
                field: 'failed_hosts',
                content: {
                    label: '',
                    nosort: true,
                    mode: 'all',
                    iconOnly: true,
                    awToolTip: "{{ nested_group.hosts_status_tip }}",
                    dataPlacement: "top",
                    icon: "{{ 'fa icon-job-' + nested_group.hosts_status_class }}",
                    columnClass: 'status-column'
                }
            }
        ],

        fields: {
            name: {
                label: i18n._('Groups'),
                key: true,
                ngClick: "goToGroupGroups(nested_group.id)",
                columnClass: 'col-lg-6 col-md-6 col-sm-6 col-xs-6',
                class: 'InventoryManage-breakWord',
            }
        },

        actions: {
            refresh: {
                mode: 'all',
                awToolTip: i18n._("Refresh the page"),
                ngClick: "refreshGroups()",
                ngShow: "socketStatus == 'error'",
                actionClass: 'btn List-buttonDefault',
                buttonContent: i18n._('REFRESH')
            },
            launch: {
                mode: 'all',
                ngDisabled: '!groupsSelected',
                ngClick: 'setAdhocPattern()',
                awToolTip: i18n._("Select an inventory source by clicking the check box beside it. The inventory source can be a single group or host, a selection of multiple hosts, or a selection of multiple groups."),
                dataPlacement: 'top',
                actionClass: 'btn List-buttonDefault',
                buttonContent: i18n._('RUN COMMANDS'),
                showTipWhenDisabled: true,
                tooltipInnerClass: "Tooltip-wide",
                ngShow: 'canAdhoc'
                // TODO: set up a tip watcher and change text based on when
                // things are selected/not selected.  This is started and
                // commented out in the inventory controller within the watchers.
                // awToolTip: "{{ adhocButtonTipContents }}",
                // dataTipWatch: "adhocButtonTipContents"
            },
            associate: {
                mode: 'all',
                ngClick: 'associateGroup()',
                awToolTip: i18n._("Associate an existing group"),
                actionClass: 'at-Button--add',
                actionId: 'button-add',
                ngShow: 'canAdd',
                dataPlacement: "top",
            }
        },

        fieldActions: {

            columnClass: 'col-lg-6 col-md-6 col-sm-6 col-xs-6 text-right',

            edit: {
                mode: 'all',
                ngClick: "editGroup(nested_group.id)",
                awToolTip: i18n._('Edit group'),
                dataPlacement: "top",
                ngShow: "nested_group.summary_fields.user_capabilities.edit"
            },
            view: {
                mode: 'all',
                ngClick: "editGroup(nested_group.id)",
                awToolTip: i18n._('View group'),
                dataPlacement: "top",
                ngShow: "!nested_group.summary_fields.user_capabilities.edit"
            },
            "delete": {
                mode: 'all',
                ngClick: "disassociateGroup(nested_group)",
                awToolTip: i18n._('Disassociate group'),
                iconClass: 'fa fa-times',
                dataPlacement: "top",
                ngShow: "nested_group.summary_fields.user_capabilities.delete"
            }
        }
    };
}];
