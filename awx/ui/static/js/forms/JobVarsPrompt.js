/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobVarsPrompt.js
 *  
 *  Form definition used during job submission to prompt for extra vars 
 *  
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
            variables: {
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