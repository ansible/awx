/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  ProjectStatus.js
 *  Form definition for Project Status -JSON view
 *
 *  
 */
angular.module('ProjectStatusDefinition', [])
    .value(
    'ProjectStatusForm', {
    
        name: 'project_update',
        editTitle: 'SCM Status', 
        well: false,
        'class': 'horizontal-narrow',

        fields: {
            created: {
                label: 'Created', 
                type: 'text',
                readonly: true
            },
            status: {
                label: 'Status',
                type: 'text',
                readonly: true
            },
            result_stdout: {
                label: 'Std Out', 
                type: 'textarea',
                ngShow: "result_stdout",
                'class': 'mono-space',
                readonly: true,
                rows: 15
            },
            result_traceback: {
                label: 'Traceback', 
                type: 'textarea',
                ngShow: "result_traceback",
                'class': 'mono-space',
                readonly: true,
                rows: 15
            }
        }
    }); //Form
