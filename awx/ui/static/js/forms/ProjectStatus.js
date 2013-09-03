/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
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
        editTitle: 'Latest SCM Update', 
        well: false,
        'class': 'horizontal-narrow',

        fields: {
            name: {
                label: 'Name', 
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
                readonly: true,
                rows: 15
            },
            result_traceback: {
                label: 'Traceback', 
                type: 'textarea',
                ngShow: "result_traceback",
                readonly: true,
                rows: 15
            }
        }
    }); //Form
