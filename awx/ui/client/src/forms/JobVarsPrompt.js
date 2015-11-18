/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 
/**
 * @ngdoc function
 * @name forms.function:JobVarsPrompt
 * @description This form is for job variables prompt modal
*/

export default
    angular.module('JobVarsPromptFormDefinition', [])

        .value ('JobVarsPromptForm', {

            addTitle: '',
            editTitle: '',
            name: 'job',
            well: false,

            actions: { },

            fields: {
                extra_vars: {
                    label: null,
                    type: 'textarea',
                    rows: 6,
                    addRequired: false,
                    editRequired: false,
                    "default": "---"
                }
            },

            buttons: { },

            related: { }

        });
