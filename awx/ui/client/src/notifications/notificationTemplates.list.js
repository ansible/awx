/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/



export default function(){
    return {
        name:  'notifiers' ,
        listTitle: 'Notification Templates',
        iterator: 'notifier',
        index: false,
        hover: false,

        fields: {
            status: {
                label: '',
                columnClass: 'List-staticColumn--smallStatus',
                searchable: false,
                nosort: true,
                ngClick: "null",
                iconOnly: true,
                excludeModal: true,
                icons: [{
                    icon: "{{ 'icon-job-' + notifier.status }}",
                    awToolTip: "Click for recent notifications",
                    awTipPlacement: "right",
                    ngClick: "showSummary($event, notifier.id)",
                    ngClass: ""
                }]
            },
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-md-3 col-sm-9 col-xs-9',
                linkTo: '/#/notifications/{{notifier.id}}'
            },
            notification_type: {
                    label: 'Type',
                    searchType: 'select',
                    searchOptions: [], // will be set by Options call to projects resource
                    excludeModal: true,
                    columnClass: 'col-md-4 hidden-sm hidden-xs'
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addNotification()',
                awToolTip: 'Create a new custom inventory',
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ADD'
            }
        },

        fieldActions: {

            columnClass: 'col-md-2 col-sm-3 col-xs-3',
            test: {
                ngClick: "testNotification(notification.id)",
                icon: 'fa-bell-o',
                label: 'Edit',
                "class": 'btn-sm',
                awToolTip: 'Test notification',
                dataPlacement: 'top'
            },
            edit: {
                ngClick: "editNotification(notification.id)",
                icon: 'fa-edit',
                label: 'Edit',
                "class": 'btn-sm',
                awToolTip: 'Edit notification',
                dataPlacement: 'top'
            },
            "delete": {
                ngClick: "deleteNotification(notifier.id, notifier.name)",
                icon: 'fa-trash',
                label: 'Delete',
                "class": 'btn-sm',
                awToolTip: 'Delete notification',
                dataPlacement: 'top'
            }
        }
    };
}
