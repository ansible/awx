/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  JobTemplates.js 
 *  List view object for Job Templates data model.
 *
 *
 */
angular.module('JobTemplatesListDefinition', [])
    .value(
    'JobTemplateList', {
        
        name: 'job_templates',
        iterator: 'job_template',
        selectTitle: 'Add Job Template',
        editTitle: 'Job Templates',
        selectInstructions: 'Click on a row to select it, and click Finished when done. Use the green <i class=\"icon-plus\"></i> button to create a new row.', 
        index: true,
        
        fields: {
            name: {
                key: true,
                label: 'Name'
                },
            description: {
                label: 'Description'
                }
            },
        
        actions: {
            add: {
                icon: 'icon-plus',
                mode: 'all',                // One of: edit, select, all
                ngClick: 'addJobTemplate()',
                class: 'btn-success',
                basePaths: ['job_templates'], 
                awToolTip: 'Create a new template'
                }
            },

        fieldActions: {
            edit: {
                ngClick: "editJobTemplate(\{\{ job_template.id \}\})",
                icon: 'icon-edit',
                awToolTip: 'View/Edit template',
                class: 'btn-mini'
                },
            submit: {
                icon: 'icon-play',
                mode: 'all',
                class: 'btn-mini btn-success',
                ngClick: 'submitJob(\{\{ job_template.id \}\})',
                awToolTip: 'Create and run a job using this template'     
                },
            delete: {
                ngClick: "deleteJobTemplate(\{\{ job_template.id \}\},'\{\{ job_template.name \}\}')",
                icon: 'icon-remove',
                class: 'btn-danger btn-mini',
                awToolTip: 'Delete template'
                }
            }
        });
