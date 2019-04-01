/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {
        name: 'configuration_saml_template',
        showActions: true,
        showHeader: false,

        fields: {
            SOCIAL_AUTH_SAML_CALLBACK_URL: {
                type: 'text',
                reset: 'SOCIAL_AUTH_SAML_CALLBACK_URL'
            },
            SOCIAL_AUTH_SAML_METADATA_URL: {
                type: 'text',
                reset: 'SOCIAL_AUTH_SAML_METADATA_URL'
            },
            SOCIAL_AUTH_SAML_SP_ENTITY_ID: {
                type: 'text',
                reset: 'SOCIAL_AUTH_SAML_SP_ENTITY_ID'
            },
            SOCIAL_AUTH_SAML_SP_PUBLIC_CERT: {
                type: 'textarea',
                rows: 6,
                elementClass: 'Form-monospace',
                reset: 'SOCIAL_AUTH_SAML_SP_PUBLIC_CERT'
            },
            SOCIAL_AUTH_SAML_SP_PRIVATE_KEY: {
                type: 'textarea',
                rows: 6,
                elementClass: 'Form-monospace',
                hasShowInputButton: true,
                reset: 'SOCIAL_AUTH_SAML_SP_PRIVATE_KEY'
            },
            SOCIAL_AUTH_SAML_ORG_INFO: {
                type: 'textarea',
                reset: 'SOCIAL_AUTH_SAML_ORG_INFO',
                rows: 6,
                codeMirror: true,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth'
            },
            SOCIAL_AUTH_SAML_TECHNICAL_CONTACT: {
                type: 'textarea',
                reset: 'SOCIAL_AUTH_SAML_TECHNICAL_CONTACT',
                rows: 6,
                codeMirror: true,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth'
            },
            SOCIAL_AUTH_SAML_SUPPORT_CONTACT: {
                type: 'textarea',
                reset: 'SOCIAL_AUTH_SAML_SUPPORT_CONTACT',
                rows: 6,
                codeMirror: true,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth'
            },
            SOCIAL_AUTH_SAML_ENABLED_IDPS: {
                type: 'textarea',
                reset: 'SOCIAL_AUTH_SAML_ENABLED_IDPS',
                rows: 6,
                codeMirror: true,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth'
            },
            SOCIAL_AUTH_SAML_ORGANIZATION_MAP: {
                type: 'textarea',
                reset: 'SOCIAL_AUTH_SAML_ORGANIZATION_MAP',
                rows: 6,
                codeMirror: true,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth'
            },
            SOCIAL_AUTH_SAML_ORGANIZATION_ATTR: {
                type: 'textarea',
                reset: 'SOCIAL_AUTH_SAML_ORGANIZATION_ATTR',
                rows: 6,
                codeMirror: true,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth'
            },
            SOCIAL_AUTH_SAML_TEAM_MAP: {
                type: 'textarea',
                reset: 'SOCIAL_AUTH_SAML_TEAM_MAP',
                rows: 6,
                codeMirror: true,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth'
            },
            SOCIAL_AUTH_SAML_TEAM_ATTR: {
                type: 'textarea',
                reset: 'SOCIAL_AUTH_SAML_TEAM_ATTR',
                rows: 6,
                codeMirror: true,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth'
            },
            SOCIAL_AUTH_SAML_SECURITY_CONFIG: {
                type: 'textarea',
                reset: 'SOCIAL_AUTH_SAML_SECURITY_CONFIG',
                codeMirror: true,
                rows: 6,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
            },
            SOCIAL_AUTH_SAML_SP_EXTRA: {
                type: 'textarea',
                reset: 'SOCIAL_AUTH_SAML_SP_EXTRA',
                codeMirror: true,
                rows: 6,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
            },
            SOCIAL_AUTH_SAML_EXTRA_DATA: {
                type: 'textarea',
                reset: 'SOCIAL_AUTH_SAML_EXTRA_DATA',
                codeMirror: true,
                rows: 6,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
            },
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
                ngDisabled: "configuration_saml_template_form.$invalid || configuration_saml_template_form.$pending"
            }
        }
    };
}
];
