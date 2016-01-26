/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('JobTemplatesListDefinition', [])
    .value('JobTemplateList', {

        name: 'job_templates',
        iterator: 'job_template',
        selectTitle: 'Add Job Template',
        editTitle: 'Job Templates',
        listTitle: 'Job Templates',
        selectInstructions: "Click on a row to select it, and click Finished when done. Use the <i class=\"icon-plus\"></i> " +
            "button to create a new job template.",
        index: false,
        hover: true,

        fields: {
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-lg-3 col-md-3 col-sm-4 col-xs-4'
            },
            description: {
                label: 'Description',
                columnClass: 'col-lg-3 col-md-3 hidden-sm hidden-xs'
            },
            smart_status: {
              label: 'Activity',
              columnClass: 'List-tableCell col-lg-4 col-md-4 col-sm-5 col-xs-5',
              searchable: false,
              nosort: true,
              ngInclude: "'/static/partials/job-template-smart-status.html'",
              type: 'template'
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addJobTemplate()',
                basePaths: ['job_templates'],
                awToolTip: 'Create a new template',
                ngHide: 'portalMode===true',
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ADD'
            }
        },

        fieldActions: {

            columnClass: 'col-lg-2 col-md-2 col-sm-3 col-xs-3',

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
            copy: {
                label: 'Copy',
                ngClick: "copyJobTemplate(job_template.id, job_template.name)",
                "class": 'btn-danger btn-xs',
                awToolTip: 'Copy template',
                dataPlacement: 'top',
                ngHide: 'job_template.summary_fields.can_copy===false'
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
            }
        }
    });
