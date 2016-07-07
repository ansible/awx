/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default function(){
    return {
        // These tooltip fields are consumed to build disabled related tabs tooltips in the form > add view
        dataPlacement: 'top',
        awToolTip: 'Please save before adding notifications',
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
            notification_templates_success: {
                label: 'Successful',
                flag: 'notification_templates_success',
                type: "toggle",
                ngClick: "toggleNotification($event, notification.id, \"notification_templates_success\")",
                awToolTip: "{{ schedule.play_tip }}",
                dataTipWatch: "schedule.play_tip",
                dataPlacement: "right",
                searchable: false,
                nosort: true,
            },
            notification_templates_error: {
                label: 'Failed',
                columnClass: 'NotifierList-lastColumn',
                flag: 'notification_templates_error',
                type: "toggle",
                ngClick: "toggleNotification($event, notification.id, \"notification_templates_error\")",
                awToolTip: "{{ schedule.play_tip }}",
                dataTipWatch: "schedule.play_tip",
                dataPlacement: "right",
                searchable: false,
                nosort: true,
            }
        }

    };
}
