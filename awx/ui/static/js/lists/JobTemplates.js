/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobTemplates.js
 *  List view object for Job Templates data model.
 *
 *
 */



export default
    angular.module('JobTemplatesListDefinition', [])
    .value('JobTemplateList', {

        name: 'job_templates',
        iterator: 'job_template',
        selectTitle: 'Add Job Template',
        editTitle: 'Job Templates',
        selectInstructions: "Click on a row to select it, and click Finished when done. Use the <i class=\"icon-plus\"></i> " +
            "button to create a new job template.",
        index: false,
        hover: true,

        fields: {
          smart_status: {
              label: 'Status',
              columnClass: 'col-md-2 col-sm-2 col-xs-2',
              searchable: false,
              nosort: true,
              ngClick: "null",
              smartStatus: true
            },
            name: {
                key: true,
                label: 'Name',
                // columnClass: 'col-lg-5 col-md-5 col-sm-9 col-xs-8'
            },
            description: {
                label: 'Description',
                // columnClass: 'col-lg-4 col-md-3 hidden-sm hidden-xs'
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addJobTemplate()',
                basePaths: ['job_templates'],
                awToolTip: 'Create a new template',
                ngHide: 'portalMode===true'
            },
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                icon: "icon-comments-alt",
                mode: 'edit',
                ngHide: 'portalMode===true'
            }
        },

        fieldActions: {
            submit: {
                label: 'Launch',
                mode: 'all',
                ngClick: 'submitJob(job_template.id)',
                awToolTip: 'Start a job using this template',
                dataPlacement: 'top'
            },
            schedule: {
                label: 'Schedule',
                mode: 'all',
                ngHref: '#/job_templates/{{ job_template.id }}/schedules',
                awToolTip: 'Schedule future job template runs',
                dataPlacement: 'top',
            },
            edit: {
                label: 'Edit',
                ngClick: "editJobTemplate(job_template.id)",
                awToolTip: 'Edit template',
                "class": 'btn-default btn-xs',
                dataPlacement: 'top',
            },
            "delete": {
                label: 'Delete',
                ngClick: "deleteJobTemplate(job_template.id, job_template.name)",
                "class": 'btn-danger btn-xs',
                awToolTip: 'Delete template',
                dataPlacement: 'top',
            },
            copy: {
                label: 'Copy',
                ngClick: "copyJobTemplate(job_template.id, job_template.name)",
                "class": 'btn-danger btn-xs',
                awToolTip: 'Copy template',
                dataPlacement: 'top',
                ngHide: 'job_template.summary_fields.can_copy===false'

            }
        }
    });
