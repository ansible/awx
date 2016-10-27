/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default function() {
    return {
        name: 'configuration_google_oauth_template',
        showActions: true,
        showHeader: false,

        fields: {
            SOCIAL_AUTH_GOOGLE_OAUTH2_KEY: {
                type: 'text',
                reset: 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY'
            },
            SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET: {
                type: 'text',
                reset: 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET'
            },
            SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS: {
                type: 'textarea',
                reset: 'SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS',
                rows: 6
            },
            SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS: {
                type: 'textarea',
                reset: 'SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS',
                codeMirror: true,
                rows: 6,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
            }
        },

        buttons: {
            reset: {
                ngClick: 'vm.resetAllConfirm()',
                label: 'Reset All',
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
