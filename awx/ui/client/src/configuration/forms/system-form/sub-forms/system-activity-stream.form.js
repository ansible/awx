/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default ['i18n', function(i18n) {
     return {
         name: 'configuration_activity_stream_template',
         showActions: true,
         showHeader: false,

         fields: {
             ACTIVITY_STREAM_ENABLED: {
                 type: 'toggleSwitch',
             },
             ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC: {
                 type: 'toggleSwitch'
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
