/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {
        showHeader: false,
        name: 'configuration_system_template',
        showActions: true,

        fields: {
            TOWER_URL_BASE: {
                type: 'text',
                reset: 'TOWER_URL_BASE',
            },
            TOWER_ADMIN_ALERTS: {
                type: 'toggleSwitch',
            },
            ACTIVITY_STREAM_ENABLED: {
                type: 'toggleSwitch',
            },
            ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC: {
                type: 'toggleSwitch'
            },
            ORG_ADMINS_CAN_SEE_ALL_USERS: {
                type: 'toggleSwitch',
            },
            // LICENSE: {
            //     type: 'textarea',
            //     rows: 6,
            //     codeMirror: true,
            //     class: 'Form-textAreaLabel Form-formGroup--fullWidth'
            // }
        },

        buttons: {
            reset: {
                ngClick: 'vm.resetAllConfirm()',
                label: i18n._('Reset All'),
                class: 'Form-button--left Form-cancelButton'
            },
            cancel: {
                ngClick: 'vm.formCancel()',
            },
            save: {
                ngClick: 'vm.formSave()',
                ngDisabled: true
            }
        }
    };
}
];
