/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 /**
  * This is the list definition for the notification templates list
  * off of the settings page
  */

export default function(){
    return {
        name:  'notification_templates' ,
        listTitle: 'Notification Templates',
        iterator: 'notification_template',
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
                    icon: "{{ 'icon-job-' + notification_template.status }}",
                    ngClick: "showSummary($event, notification_template.id)",
                    ngClass: ""
                }]
            },
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-md-3 col-sm-9 col-xs-9',
                linkTo: '/#/notification_templates/{{notification_template.id}}'
            },
            notification_type: {
                    label: 'Type',
                    searchType: 'select',
                    searchOptions: [],
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
                ngClick: "testNotification(notification_template.id)",
                icon: 'fa-bell-o',
                label: 'Edit',
                "class": 'btn-sm',
                awToolTip: 'Test notification',
                dataPlacement: 'top'
            },
            edit: {
                ngClick: "editNotification(notification_template.id)",
                icon: 'fa-edit',
                label: 'Edit',
                "class": 'btn-sm',
                awToolTip: 'Edit notification',
                dataPlacement: 'top'
            },
            "delete": {
                ngClick: "deleteNotification(notification_template.id, notification_template.name)",
                icon: 'fa-trash',
                label: 'Delete',
                "class": 'btn-sm',
                awToolTip: 'Delete notification',
                dataPlacement: 'top'
            }
        }
    };
}
