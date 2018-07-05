/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {
        showHeader: false,
        name: 'configuration_ui_template',
        showActions: true,

        fields: {
            PENDO_TRACKING_STATE: {
                type: 'select',
                ngChange: 'changedPendo()',
                ngOptions: 'choice.label for choice in PENDO_TRACKING_STATE_options track by choice.value',
                reset: 'PENDO_TRACKING_STATE'
            },
            CUSTOM_LOGO: {
                type: 'custom',
                reset: 'CUSTOM_LOGO',
                control: `<image-upload key="CUSTOM_LOGO"></image-upload>`
            },
            CUSTOM_LOGIN_INFO: {
                type: 'textarea',
                reset: 'CUSTOM_LOGIN_INFO',
                rows: 6
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
