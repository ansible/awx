/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default ['i18n', function(i18n) {
     return {
         name: 'configuration_logging_template',
         showActions: true,
         showHeader: false,

         fields: {
             LOG_AGGREGATOR_HOST: {
                 type: 'text',
                 reset: 'LOG_AGGREGATOR_HOST'
             },
             LOG_AGGREGATOR_PORT: {
                 type: 'text',
                 reset: 'LOG_AGGREGATOR_PORT'
             },
             LOG_AGGREGATOR_TYPE: {
                 type: 'select',
                 reset: 'LOG_AGGREGATOR_TYPE',
                 ngOptions: 'type.label for type in LOG_AGGREGATOR_TYPE_options track by type.value',
             },
             LOG_AGGREGATOR_USERNAME: {
                 type: 'text',
                 reset: 'LOG_AGGREGATOR_USERNAME'
             },
             LOG_AGGREGATOR_PASSWORD: {
                 type: 'sensitive',
                 hasShowInputButton: true,
                 reset: 'LOG_AGGREGATOR_PASSWORD'
             },
             LOG_AGGREGATOR_LOGGERS: {
                 type: 'textarea',
                 reset: 'LOG_AGGREGATOR_LOGGERS'
             },
            LOG_AGGREGATOR_INDIVIDUAL_FACTS: {
                type: 'toggleSwitch',
            },
            LOG_AGGREGATOR_PROTOCOL: {
                type: 'select',
                reset: 'LOG_AGGREGATOR_PROTOCOL',
                ngOptions: 'type.label for type in LOG_AGGREGATOR_PROTOCOL_options track by type.value',
                disableChooseOption: true
            },
            LOG_AGGREGATOR_TCP_TIMEOUT: {
                type: 'text',
                reset: 'LOG_AGGREGATOR_TCP_TIMEOUT',
                ngShow: 'LOG_AGGREGATOR_PROTOCOL.value === "tcp" || LOG_AGGREGATOR_PROTOCOL.value === "https"',
                awRequiredWhen: {
                    reqExpression: "LOG_AGGREGATOR_PROTOCOL.value === 'tcp' || LOG_AGGREGATOR_PROTOCOL.value === 'https'",
                    init: "false"
                },
            },
            LOG_AGGREGATOR_LEVEL: {
                type: 'select',
                reset: 'LOG_AGGREGATOR_LEVEL',
                ngOptions: 'type.label for type in LOG_AGGREGATOR_LEVEL_options track by type.value',
                disableChooseOption: true
            },
            LOG_AGGREGATOR_VERIFY_CERT: {
                type: 'toggleSwitch',
                ngShow: "LOG_AGGREGATOR_PROTOCOL.value === 'https'"
            }
         },

         buttons: {
             reset: {
                 ngShow: '!user_is_system_auditor',
                 ngClick: 'vm.resetAllConfirm()',
                 label: i18n._('Revert all to default'),
                 class: 'Form-resetAll'
             },
             testLogging: {
                 ngClass: "{'Form-button--disabled': vm.disableTestButton}",
                 ngClick: 'vm.testLogging()',
                 label: i18n._('Test'),
                 class: 'Form-primaryButton',
                 awToolTip: '{{vm.testTooltip}}',
                 dataTipWatch: 'vm.testTooltip',
                 dataPlacement: 'top',
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
