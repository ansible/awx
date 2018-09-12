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
        ngIf: 'current_user.is_superuser || isOrgAdmin || isNotificationAdmin',
        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-md-4 col-sm-9 col-xs-9',
                linkTo: '/#/notification_templates/{{notification.id}}'
            },
            notification_type: {
                label: i18n._('Type'),
                searchType: 'select',
                searchOptions: [],
                excludeModal: true,
                columnClass: 'd-none d-sm-flex col-md-4 col-sm-3'
            },
            notification_templates_success: {
                label: i18n._('Success'),
                flag: 'notification_templates_success',
                type: "toggle",
                ngClick: "toggleNotification($event, notification.id, \"notification_templates_success\")",
                ngDisabled: "!(current_user.is_superuser || isOrgAdmin)",
                awToolTip: "{{ schedule.play_tip }}",
                dataTipWatch: "schedule.play_tip",
                dataPlacement: "right",
                nosort: true,
                columnClass: 'd-none d-md-flex justify-content-start col-md-2'
            },
            notification_templates_error: {
                label: i18n._('Failure'),
                columnClass: 'd-none d-md-flex justify-content-start col-md-2 NotifierList-lastColumn',
                flag: 'notification_templates_error',
                type: "toggle",
                ngClick: "toggleNotification($event, notification.id, \"notification_templates_error\")",
                ngDisabled: "!(current_user.is_superuser || isOrgAdmin)",
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
                ngShow: 'current_user.is_superuser || (current_user_admin_orgs && current_user_admin_orgs.length > 0)'
            }
        }

    };
}];
