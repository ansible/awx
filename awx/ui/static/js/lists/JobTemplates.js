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
                "class": 'btn-success btn-xs',
                basePaths: ['job_templates'], 
                awToolTip: 'Create a new template'
                },
            reset: {
                dataPlacement: 'top',
                icon: "icon-undo",
                mode: 'all',
                'class': 'btn-xs btn-primary',
                awToolTip: "Reset the search filter",
                ngClick: "resetSearch()",
                iconSize: 'large'
                },
            stream: {
                'class': "btn-primary btn-xs activity-btn",
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                dataPlacement: "top",
                icon: "icon-comments-alt",
                mode: 'all',
                iconSize: 'large',
                ngShow: "user_is_superuser"
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editJobTemplate(\{\{ job_template.id \}\})",
                icon: 'icon-edit',
                awToolTip: 'Edit template',
                "class": 'btn-default btn-xs'
                },
            submit: {
                label: 'Launch',
                icon: 'icon-rocket',
                mode: 'all',
                "class": 'btn-xs btn-success',
                ngClick: 'submitJob(\{\{ job_template.id \}\})',
                awToolTip: 'Start a job using this template'     
                },
            "delete": {
                label: 'Delete',
                ngClick: "deleteJobTemplate(\{\{ job_template.id \}\},'\{\{ job_template.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-danger btn-xs',
                awToolTip: 'Delete template'
                }
            }
        });
