/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
  return {
      name: 'configuration_authMisc_template',
      showActions: true,
      showHeader: false,

      fields: {
          ACCESS_TOKEN_EXPIRE_SECONDS: {
              type: 'text',
              reset: 'ACCESS_TOKEN_EXPIRE_SECONDS'
          },
          AUTHORIZATION_CODE_EXPIRE_SECONDS: {
              type: 'text',
              reset: 'AUTHORIZATION_CODE_EXPIRE_SECONDS'
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
              ngDisabled: "!enterprise_auth || configuration_authMisc_template_form.$invalid || configuration_authMisc_template_form.$pending"
          }
      }
  };
}
];
