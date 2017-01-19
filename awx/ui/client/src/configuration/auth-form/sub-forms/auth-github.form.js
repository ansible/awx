/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
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
                type: 'sensitive',
                hasShowInputButton: true,
                reset: 'SOCIAL_AUTH_GITHUB_SECRET'
            }
        },

        buttons: {
            reset: {
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
