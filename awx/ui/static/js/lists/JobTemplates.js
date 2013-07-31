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
        hover: true,
        
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
                label: 'Create New',
                icon: 'icon-plus',
                mode: 'all',                // One of: edit, select, all
                ngClick: 'addJobTemplate()',
                "class": 'btn-success btn-small',
                basePaths: ['job_templates'], 
                awToolTip: 'Create a new template'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editJobTemplate(\{\{ job_template.id \}\})",
                icon: 'icon-edit',
                awToolTip: 'Edit template',
                "class": 'btn-small'
                },
            submit: {
                label: 'Launch',
                icon: 'icon-rocket',
                mode: 'all',
                "class": 'btn-small btn-success',
                ngClick: 'submitJob(\{\{ job_template.id \}\})',
                awToolTip: 'Start a job using this template'     
                },
            "delete": {
                label: 'Delete',
                ngClick: "deleteJobTemplate(\{\{ job_template.id \}\},'\{\{ job_template.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-danger btn-small',
                awToolTip: 'Delete template'
                }
            }
        });
