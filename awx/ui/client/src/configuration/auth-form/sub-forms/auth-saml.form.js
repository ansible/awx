/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default function() {
    return {
        name: 'configuration_saml_template',
        showActions: true,
        showHeader: false,

        fields: {
            SOCIAL_AUTH_SAML_SP_ENTITY_ID: {
                type: 'text',
                reset: 'SOCIAL_AUTH_SAML_SP_ENTITY_ID'
            },
            SOCIAL_AUTH_SAML_SP_PUBLIC_CERT: {
                type: 'text',
                reset: 'SOCIAL_AUTH_SAML_SP_PUBLIC_CERT'
            },
            SOCIAL_AUTH_SAML_SP_PRIVATE_KEY: {
                type: 'text',
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
