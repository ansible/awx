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
                type: 'text',
                reset: 'RADIUS_SECRET'
            }
        },

        buttons: {
            reset: {
                ngClick: 'vm.resetAllConfirm()',
                label: i18n._('Reset All'),
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
];
