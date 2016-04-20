/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default function(){
    return {
        name:  'notifications' ,
        title: 'Notifications',
        iterator: 'notification',
        index: false,
        hover: false,
        basePath: 'notifications',
        fields: {
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-md-3 col-sm-9 col-xs-9',
                linkTo: '/#/notifications/{{notifier.id}}',
            },
            notification_type: {
                label: 'Type',
                searchType: 'select',
                searchOptions: [],
                excludeModal: true,
                columnClass: 'col-md-4 hidden-sm hidden-xs'
            },
            notifiers_success: {
                label: 'Successful',
                flag: 'notifiers_success',
                type: "toggle",
                ngClick: "toggleNotification($event, notification.id, \"notifiers_success\")",
                awToolTip: "{{ schedule.play_tip }}",
                dataTipWatch: "schedule.play_tip",
                dataPlacement: "right",
                searchable: false,
                nosort: true,
            },
            notifiers_error: {
                label: 'Failed',
                columnClass: 'NotifierList-lastColumn',
                flag: 'notifiers_error',
                type: "toggle",
                ngClick: "toggleNotification($event, notification.id, \"notifiers_error\")",
                awToolTip: "{{ schedule.play_tip }}",
                dataTipWatch: "schedule.play_tip",
                dataPlacement: "right",
                searchable: false,
                nosort: true,
            }
        }

    };
}
