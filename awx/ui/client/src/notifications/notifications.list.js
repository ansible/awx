/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 /**
  * This is the list definition for the notification templates list
  * used in the related tabs
  */

export default ['i18n', 'templateUrl', function(i18n, templateUrl){
    return {
        // These tooltip fields are consumed to build disabled related tabs tooltips in the form > add view
        dataPlacement: 'top',
        awToolTip: i18n._('Please save before adding notifications.'),
        name:  'notifications' ,
        title: i18n._('Notifications'),
        iterator: 'notification',
        index: false,
        hover: false,
        emptyListText: i18n.sprintf(i18n._("This list is populated by notification templates added from the %sNotifications%s section"), "&nbsp;<a ui-sref='notifications.add'>", "</a>&nbsp;"),
        basePath: 'notification_templates',
        ngIf: 'sufficientRoleForNotif',
        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-sm-9 col-xs-9',
                linkTo: '/#/notification_templates/{{notification.id}}',
                columnNgClass: "{'col-lg-4 col-md-2': showApprovalColumn, 'col-lg-5 col-md-3': !showApprovalColumn}"
            },
            notification_type: {
                label: i18n._('Type'),
                searchType: 'select',
                searchOptions: [],
                excludeModal: true,
                columnClass: 'd-none d-sm-flex col-lg-4 col-md-2 col-sm-3',
            },
            notification_templates_approvals: {
                label: i18n._('Approval'),
                columnClass: 'd-none d-md-flex justify-content-start col-lg-1 col-md-2',
                flag: 'notification_templates_approvals',
                type: "toggle",
                ngClick: "toggleNotification($event, notification.id, 'notification_templates_approvals')",
                ngDisabled: "!sufficientRoleForNotifToggle",
                awToolTip: "{{ schedule.play_tip }}",
                dataTipWatch: "schedule.play_tip",
                dataPlacement: "right",
                nosort: true,
                ngIf: "showApprovalColumn"
            },
            notification_templates_started: {
                label: i18n._("Start"),
                flag: 'notification_templates_started',
                type: "toggle",
                ngClick: "toggleNotification($event, notification.id, 'notification_templates_started')",
                ngDisabled: "!sufficientRoleForNotifToggle",
                awToolTip: "{{ schedule.play_tip }}",
                dataTipWatch: "schedule.play_tip",
                dataPlacement: "right",
                nosort: true,
                columnClass: 'd-none d-md-flex justify-content-start col-lg-1 col-md-2'
            },
            notification_templates_success: {
                label: i18n._('Success'),
                flag: 'notification_templates_success',
                type: "toggle",
                ngClick: "toggleNotification($event, notification.id, 'notification_templates_success')",
                ngDisabled: "!sufficientRoleForNotifToggle",
                awToolTip: "{{ schedule.play_tip }}",
                dataTipWatch: "schedule.play_tip",
                dataPlacement: "right",
                nosort: true,
                columnClass: 'd-none d-md-flex justify-content-start col-lg-1 col-md-2'
            },
            notification_templates_error: {
                label: i18n._('Failure'),
                columnClass: 'd-none d-md-flex justify-content-start col-lg-1 col-md-2 NotifierList-lastColumn',
                flag: 'notification_templates_error',
                type: "toggle",
                ngClick: "toggleNotification($event, notification.id, 'notification_templates_error')",
                ngDisabled: "!sufficientRoleForNotifToggle",
                awToolTip: "{{ schedule.play_tip }}",
                dataTipWatch: "schedule.play_tip",
                dataPlacement: "right",
                nosort: true
            }
        },
        actions: {
            add: {
                type: 'template',
                template: templateUrl('notifications/notification-templates-list/add-notifications-action'),
                ngShow: 'isNotificationAdmin'
            }
        }

    };
}];
