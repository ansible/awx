/*************************************************
 * Copyright (c) 2016 Ansible, Inc. (copied from auth-google-oauth2.form.js)
 * Copyright (c) 2020 Luther Systems, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {
        name: 'configuration_cognito_oauth_template',
        showActions: true,
        showHeader: false,

        fields: {
            SOCIAL_AUTH_COGNITO_CALLBACK_URL: {
                type: 'text',
                reset: 'SOCIAL_AUTH_COGNITO_CALLBACK_URL'
            },
            SOCIAL_AUTH_COGNITO_POOL_DOMAIN: {
                type: 'text',
                reset: 'SOCIAL_AUTH_COGNITO_POOL_DOMAIN'
            },
            SOCIAL_AUTH_COGNITO_KEY: {
                type: 'text',
                reset: 'SOCIAL_AUTH_COGNITO_KEY'
            },
            SOCIAL_AUTH_COGNITO_SECRET: {
                type: 'sensitive',
                hasShowInputButton: true,
                reset: 'SOCIAL_AUTH_COGNITO_SECRET'
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
