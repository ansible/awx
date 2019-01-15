/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 /**
  * This is the list definition for the notification templates list
  * off of the settings page
  */

export default ['i18n', function(i18n){
    return {
        name:  'notification_templates' ,
        listTitle: i18n._('NOTIFICATION TEMPLATES'),
        iterator: 'notification_template',
        index: false,
        hover: false,
        layoutClass: 'List-staticColumnLayout--statusOrCheckbox',
        staticColumns: [
            {
                field: 'status',
                content: {
                    label: '',
                    iconOnly: true,
                    nosort: true,
                    icon: 'icon-job-{{ notification_template.status }}',
                    awPopOver: '{{ notification_template.template_status_html }}',
                    dataTitle: i18n._("Recent Notifications"),
                    dataPlacement: 'right'
                }
            }
        ],

        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-md-4 col-sm-9 col-xs-9',
                linkTo: '/#/notification_templates/{{notification_template.id}}',
                awToolTip: '{{notification_template.description | sanitize}}',
                dataPlacement: 'top'
            },
            notification_type: {
                    label: i18n._('Type'),
                    ngBind: "notification_template.type_label",
                    searchType: 'select',
                    searchOptions: [],
                    excludeModal: true,
                    columnClass: 'd-none d-md-flex col-md-4'
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addNotification()',
                awToolTip: i18n._('Create a new notification template'),
                actionClass: 'at-Button--add',
                actionId: 'button-add',
                ngShow: 'canAdd'
            }
        },

        fieldActions: {

            columnClass: 'col-md-4 col-sm-3 col-xs-3',

            edit: {
                ngClick: "editNotification(notification_template.id)",
                icon: 'fa-edit',
                label: i18n._('Edit'),
                "class": 'btn-sm',
                awToolTip: i18n._('Edit notification'),
                dataPlacement: 'top',
                ngShow: 'notification_template.summary_fields.user_capabilities.edit'
            },
            test: {
                ngClick: "testNotification(notification_template.id)",
                icon: 'fa-bell-o',
                label: i18n._('Edit'),
                "class": 'btn-sm',
                awToolTip: i18n._('Test notification'),
                dataPlacement: 'top',
                ngShow: 'notification_template.summary_fields.user_capabilities.edit'
            },
            copy: {
                label: i18n._('Copy'),
                ngClick: 'copyNotification(notification_template)',
                "class": 'btn-danger btn-xs',
                awToolTip: i18n._('Copy notification'),
                dataPlacement: 'top',
                ngShow: 'notification_template.summary_fields.user_capabilities.copy'
            },
            view: {
                ngClick: "editNotification(notification_template.id)",
                label: i18n._('View'),
                "class": 'btn-sm',
                awToolTip: i18n._('View notification'),
                dataPlacement: 'top',
                ngShow: '!notification_template.summary_fields.user_capabilities.edit'
            },
            "delete": {
                ngClick: "deleteNotification(notification_template.id, notification_template.name)",
                icon: 'fa-trash',
                label: i18n._('Delete'),
                "class": 'btn-sm',
                awToolTip: i18n._('Delete notification'),
                dataPlacement: 'top',
                ngShow: 'notification_template.summary_fields.user_capabilities.delete'
            }
        }
    };
}];
