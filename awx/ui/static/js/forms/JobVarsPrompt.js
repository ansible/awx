/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobVarsPrompt.js
 *
 *  Form definition used during job submission to prompt for extra vars
 *
 */
/**
 * @ngdoc function
 * @name forms.function:JobVarsPrompt
 * @description This form is for job variables prompt modal
*/
'use strict';

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