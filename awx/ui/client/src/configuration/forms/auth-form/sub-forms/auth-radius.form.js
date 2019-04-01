/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {
        // editTitle: 'Authorization Configuration',
        name: 'configuration_radius_template',
        showActions: true,
        showHeader: false,

        fields: {
            RADIUS_SERVER: {
                type: 'text',
                reset: 'RADIUS_SERVER'
            },
            RADIUS_PORT: {
                type: 'text',
                reset: 'RADIUS_PORT'
            },
            RADIUS_SECRET: {
                type: 'sensitive',
                hasShowInputButton: true,
                reset: 'RADIUS_SECRET'
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
                ngDisabled: "configuration_radius_template_form.$invalid || configuration_radius_template_form.$pending"
            }
        }
    };
}
];
