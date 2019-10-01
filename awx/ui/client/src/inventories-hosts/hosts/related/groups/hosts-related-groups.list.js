/*************************************************
 * Copyright (c) 2017  Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {
        name: 'groups',
        iterator: 'group',
        editTitle: '{{ host.name }}',
        well: true,
        wellOverride: true,
        index: false,
        hover: true,
        trackBy: 'group.id',
        basePath:  'api/v2/hosts/{{$stateParams.host_id}}/groups/',
        layoutClass: 'List-staticColumnLayout--statusOrCheckbox',
        staticColumns: [
            {
                field: 'failed_hosts',
                content: {
                    label: '',
                    nosort: true,
                    mode: 'all',
                    iconOnly: true,
                    awToolTip: "{{ group.hosts_status_tip }}",
                    dataPlacement: "top",
                    icon: "{{ 'fa icon-job-' + group.hosts_status_class }}",
                    columnClass: 'status-column'
                }
            }
        ],

        fields: {
            name: {
                label: i18n._('Groups'),
                key: true,
                ngClick: "goToGroupGroups(group.id)",
                columnClass: 'col-lg-6 col-md-6 col-sm-6 col-xs-6',
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
            associate: {
                mode: 'all',
                ngClick: "associateGroup()",
                awToolTip: i18n._("Associate this host with a new group"),
                actionClass: 'at-Button--add',
                actionId: 'button-add',
                ngShow: 'canAdd',
                dataPlacement: "top",
            }
        },

        fieldActions: {
            columnClass: 'col-lg-6 col-md-6 col-sm-6 col-xs-6 text-right',
            "delete": {
                //label: 'Delete',
                mode: 'all',
                ngClick: "disassociateHost(group)",
                awToolTip: i18n._('Disassociate group'),
                iconClass: 'fa fa-times',
                dataPlacement: "top",
                ngShow: "group.summary_fields.user_capabilities.delete"
            }
        }
    };
}];
