/*************************************************
 * Copyright (c) 2017  Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default {
    name: 'groups',
    iterator: 'group',
    editTitle: '{{ host.name }}',
    well: true,
    wellOverride: true,
    index: false,
    hover: true,
    trackBy: 'group.id',
    basePath:  'api/v2/hosts/{{$stateParams.host_id}}/groups/',

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
        associate: {
            mode: 'all',
            ngClick: "associateGroup()",
            awToolTip: "Associate this host with a new group",
            actionClass: 'btn List-buttonSubmit',
            buttonContent: '&#43; ASSOCIATE GROUP',
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
            awToolTip: 'Disassociate host',
            dataPlacement: "top",
            ngShow: "group.summary_fields.user_capabilities.delete"
        }
    }
};
