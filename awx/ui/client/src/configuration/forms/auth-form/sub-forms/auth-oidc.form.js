/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {
        name: 'configuration_oidc_template',
        showActions: true,
        showHeader: false,

        fields: {
            SOCIAL_AUTH_OIDC_CALLBACK_URL: {
                type: 'text',
                reset: 'SOCIAL_AUTH_OIDC_CALLBACK_URL'
            },
            SOCIAL_AUTH_OIDC_KEY: {
                type: 'text',
                reset: 'SOCIAL_AUTH_OIDC_KEY'
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
