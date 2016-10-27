/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default function() {
     return {
         showHeader: false,
         name: 'configuration_jobs_template',
         showActions: true,

         fields: {
             AD_HOC_COMMANDS: {
                 type: 'select',
                 ngOptions: 'command.label for command in AD_HOC_COMMANDS_options track by command.value',
                 reset: 'AD_HOC_COMMANDS',
                 multiSelect: true
             },
             STDOUT_MAX_BYTES_DISPLAY: {
                 type: 'number',
                 reset: 'STDOUT_MAX_BYTES_DISPLAY'
             },
             AWX_PROOT_BASE_PATH: {
                 type: 'text',
                 reset: 'AWX_PROOT_BASE_PATH',
             },
             SCHEDULE_MAX_JOBS: {
                 type: 'number',
                 reset: 'SCHEDULE_MAX_JOBS'
             },
             AWX_PROOT_SHOW_PATHS: {
                 type: 'textarea',
                 reset: 'AWX_PROOT_SHOW_PATHS',
                 rows: 6
             },
             AWX_ANSIBLE_CALLBACK_PLUGINS: {
                 type: 'textarea',
                 reset: 'AWX_ANSIBLE_CALLBACK_PLUGINS',
                 rows: 6
             },
             AWX_PROOT_HIDE_PATHS: {
                 type: 'textarea',
                 reset: 'AWX_PROOT_HIDE_PATHS',
                 rows: 6
             },
             AWX_PROOT_ENABLED: {
                 type: 'toggleSwitch',
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
                // ngDisabled: true
             }
         }
     };
 }
