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
            ORG_ADMINS_CAN_SEE_ALL_USERS: {
                type: 'toggleSwitch',
            },
            MANAGE_ORGANIZATION_AUTH: {
                type: 'toggleSwitch',
            },
            SESSION_COOKIE_AGE: {
                type: 'number',
                integer: true,
                min: 61,
                reset: 'SESSION_COOKIE_AGE',
            },
            SESSIONS_PER_USER: {
                type: 'number',
                integer: true,
                spinner: true,
                min: -1,
                reset: 'SESSIONS_PER_USER',
            },
            AUTH_BASIC_ENABLED: {
                type: 'toggleSwitch',
            },
            ALLOW_OAUTH2_FOR_EXTERNAL_USERS: {
                type: 'toggleSwitch',
            },
            LOGIN_REDIRECT_OVERRIDE: {
                type: 'text',
                reset: 'LOGIN_REDIRECT_OVERRIDE'
            },
            ACCESS_TOKEN_EXPIRE_SECONDS: {
                type: 'text',
                reset: 'ACCESS_TOKEN_EXPIRE_SECONDS'
            },
            REFRESH_TOKEN_EXPIRE_SECONDS: {
                type: 'text',
                reset: 'REFRESH_TOKEN_EXPIRE_SECONDS'
            },
            AUTHORIZATION_CODE_EXPIRE_SECONDS: {
                type: 'text',
                reset: 'AUTHORIZATION_CODE_EXPIRE_SECONDS'
            },
            REMOTE_HOST_HEADERS: {
                type: 'textarea',
                reset: 'REMOTE_HOST_HEADERS'
            },
            CUSTOM_VENV_PATHS: {
                type: 'textarea',
                reset: 'CUSTOM_VENV_PATHS'
            },
            INSIGHTS_TRACKING_STATE: {
                type: 'toggleSwitch'
            },
            REDHAT_USERNAME: {
                type: 'text',
                reset: 'REDHAT_USERNAME',
            },
            REDHAT_PASSWORD: {
                type: 'sensitive',
                hasShowInputButton: true,
                reset: 'REDHAT_PASSWORD',
            },
            AUTOMATION_ANALYTICS_URL: {
                type: 'text',
                reset: 'AUTOMATION_ANALYTICS_URL',
            },
            AUTOMATION_ANALYTICS_GATHER_INTERVAL: {
                type: 'number',
                integer: true,
                min: 1800,
                reset: 'AUTOMATION_ANALYTICS_GATHER_INTERVAL',
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
