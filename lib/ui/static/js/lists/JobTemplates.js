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
        selectInstructions: 'Check the Select checkbox next to each template to be added, and click Finished when done. Use the green <i class=\"icon-plus\"></i> button to create a new template.', 
        
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
                class: 'btn btn-mini btn-success',
                basePaths: ['job_templates'], 
                awToolTip: 'Create a new template'
                }
            },

        fieldActions: {
            edit: {
                ngClick: "editJobTemplate(\{\{ job_template.id \}\})",
                icon: 'icon-edit',
                awToolTip: 'Edit user'
                },

            delete: {
                ngClick: "deleteJobTemplate(\{\{ job_template.id \}\},'\{\{ job_template.name \}\}')",
                icon: 'icon-remove',
                class: 'btn-danger',
                awToolTip: 'Delete template'
                }
            }
        });
