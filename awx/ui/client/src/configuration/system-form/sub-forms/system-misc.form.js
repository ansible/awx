/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {
        name: 'configuration_misc_template',
        showHeader: false,
        showActions: true,

        fields: {
            TOWER_URL_BASE: {
                type: 'text',
                reset: 'TOWER_URL_BASE',
            },
            TOWER_ADMIN_ALERTS: {
                type: 'toggleSwitch',
            },
            ORG_ADMINS_CAN_SEE_ALL_USERS: {
                type: 'toggleSwitch',
            },
            AUTH_TOKEN_EXPIRATION: {
                type: 'number',
                integer: true,
                min: 60,
                reset: 'AUTH_TOKEN_EXPIRATION',
            },
            AUTH_TOKEN_PER_USER: {
                type: 'number',
                integer: true,
                spinner: true,
                min: -1,
                reset: 'AUTH_TOKEN_PER_USER',
            },
            AUTH_BASIC_ENABLED: {
                type: 'toggleSwitch',
            },
            REMOTE_HOST_HEADERS: {
                type: 'textarea',
                reset: 'REMOTE_HOST_HEADERS'
            }
        },

        buttons: {
            reset: {
                ngShow: '!user_is_system_auditor',
                ngClick: 'vm.resetAllConfirm()',
                label: i18n._('Revert all to default'),
                class: 'Form-resetAll'
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
