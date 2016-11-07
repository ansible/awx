/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default function() {
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
