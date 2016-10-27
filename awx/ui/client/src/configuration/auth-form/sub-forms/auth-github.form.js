/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default function() {
    return {
        name: 'configuration_github_template',
        showActions: true,
        showHeader: false,

        fields: {
            SOCIAL_AUTH_GITHUB_KEY: {
                type: 'text',
                reset: 'SOCIAL_AUTH_GITHUB_KEY'
            },
            SOCIAL_AUTH_GITHUB_SECRET: {
                type: 'text',
                reset: 'SOCIAL_AUTH_GITHUB_SECRET'
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
