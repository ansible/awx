/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default ['i18n', function(i18n) {
     return {
         name: 'configuration_azure_template',
         showActions: true,
         showHeader: false,

         fields: {
             SOCIAL_AUTH_AZUREAD_OAUTH2_KEY: {
                 type: 'text',
                 reset: 'SOCIAL_AUTH_AZUREAD_OAUTH2_KEY'
             },
             SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET: {
                 type: 'sensitive',
                 hasShowInputButton: true,
                 reset: 'SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET'
             },
             SOCIAL_AUTH_AZUREAD_OAUTH2_ORGANIZATION_MAP: {
                 type: 'textarea',
                 reset: 'SOCIAL_AUTH_AZUREAD_OAUTH2_ORGANIZATION_MAP',
                 rows: 6,
                 codeMirror: true,
                 class: 'Form-textAreaLabel Form-formGroup--fullWidth'
             },
             SOCIAL_AUTH_AZUREAD_OAUTH2_TEAM_MAP: {
                 type: 'textarea',
                 reset: 'SOCIAL_AUTH_AZUREAD_OAUTH2_TEAM_MAP',
                 rows: 6,
                 codeMirror: true,
                 class: 'Form-textAreaLabel Form-formGroup--fullWidth'
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
