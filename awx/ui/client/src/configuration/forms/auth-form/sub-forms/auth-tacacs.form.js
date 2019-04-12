/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {
        // editTitle: 'Authorization Configuration',
        name: 'configuration_tacacs_template',
        showActions: true,
        showHeader: false,

        fields: {
            TACACSPLUS_HOST: {
                type: 'text',
                reset: 'TACACSPLUS_HOST'
            },
            TACACSPLUS_PORT: {
                type: 'text',
                reset: 'TACACSPLUS_PORT'
            },
            TACACSPLUS_SECRET: {
                type: 'sensitive',
                hasShowInputButton: true,
                reset: 'TACACSPLUS_SECRET'
            },
            TACACSPLUS_SESSION_TIMEOUT: {
                type: 'number',
                integer: true,
                spinner: true,
                min: 0,
                reset: 'TACACSPLUS_SESSION_TIMEOUT'
            },
            TACACSPLUS_AUTH_PROTOCOL: {
                type: 'select',
                reset: 'TACACSPLUS_AUTH_PROTOCOL',
                ngOptions: 'protocol.label for protocol in TACACSPLUS_AUTH_PROTOCOL_options track by protocol.value',

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
                ngDisabled: "configuration_tacacs_template_form.$invalid || configuration_tacacs_template_form.$pending"
            }
        }
    };
}
];
