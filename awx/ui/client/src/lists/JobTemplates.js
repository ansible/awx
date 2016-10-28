/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('JobTemplatesListDefinition', [])
    .factory('JobTemplateList', ['i18n', function(i18n) {
    return {

        name: 'job_templates',
        iterator: 'job_template',
        selectTitle: i18n._('Add Job Template'),
        editTitle: i18n._('Job Templates'),
        listTitle: i18n._('Job Templates'),
        selectInstructions: "Click on a row to select it, and click Finished when done. Use the <i class=\"icon-plus\"></i> " +
            "button to create a new job template.",
        index: false,
        hover: true,

        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-lg-2 col-md-2 col-sm-4 col-xs-9'
            },
            description: {
                label: i18n._('Description'),
                columnClass: 'col-lg-2 hidden-md hidden-sm hidden-xs'
            },
            smart_status: {
              label: i18n._('Activity'),
              columnClass: 'List-tableCell col-lg-2 col-md-2 hidden-sm hidden-xs',
              nosort: true,
              ngInclude: "'/static/partials/job-template-smart-status.html'",
              type: 'template'
            },
            labels: {
                label: i18n._('Labels'),
                type: 'labels',
                nosort: true,
                columnClass: 'List-tableCell col-lg-4 col-md-4 hidden-sm hidden-xs'
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addJobTemplate()',
                basePaths: ['job_templates'],
                awToolTip: i18n._('Create a new template'),
                actionClass: 'btn List-buttonSubmit',
                buttonContent: i18n._('&#43; ADD'),
                ngShow: 'canAdd'
            }
        },

        fieldActions: {

            columnClass: 'col-lg-2 col-md-3 col-sm-3 col-xs-3',

            submit: {
                label: i18n._('Launch'),
                mode: 'all',
                ngClick: 'submitJob(job_template.id)',
                awToolTip: i18n._('Start a job using this template'),
                dataPlacement: 'top',
                ngShow: 'job_template.summary_fields.user_capabilities.start'
            },
            schedule: {
                label: i18n._('Schedule'),
                mode: 'all',
                ngClick: 'scheduleJob(job_template.id)',
                awToolTip: i18n._('Schedule future job template runs'),
                dataPlacement: 'top',
                ngShow: 'job_template.summary_fields.user_capabilities.schedule'
            },
            copy: {
                label: i18n._('Copy'),
                'ui-sref': 'jobTemplates.copy({id: job_template.id})',
                "class": 'btn-danger btn-xs',
                awToolTip: i18n._('Copy template'),
                dataPlacement: 'top',
                ngShow: 'job_template.summary_fields.user_capabilities.copy'
            },
            edit: {
                label: i18n._('Edit'),
                ngClick: "editJobTemplate(job_template.id)",
                awToolTip: i18n._('Edit template'),
                "class": 'btn-default btn-xs',
                dataPlacement: 'top',
                ngShow: 'job_template.summary_fields.user_capabilities.edit'
            },
            view: {
                label: i18n._('View'),
                ngClick: "editJobTemplate(job_template.id)",
                awToolTip: i18n._('View template'),
                "class": 'btn-default btn-xs',
                dataPlacement: 'top',
                ngShow: '!job_template.summary_fields.user_capabilities.edit'
            },
            "delete": {
                label: i18n._('Delete'),
                ngClick: "deleteJobTemplate(job_template.id, job_template.name)",
                "class": 'btn-danger btn-xs',
                awToolTip: i18n._('Delete template'),
                dataPlacement: 'top',
                ngShow: 'job_template.summary_fields.user_capabilities.delete'
            }
        }
    };}]);
