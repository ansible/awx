/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default ['i18n', function(i18n) {
    return {

        name: 'templates',
        iterator: 'template',
        basePath: 'unified_job_templates',
        selectTitle: i18n._('Template'),
        editTitle: i18n._('TEMPLATES'),
        listTitle: i18n._('TEMPLATES'),
        selectInstructions: i18n.sprintf(i18n._("Click on a row to select it, and click Finished when done. Use the %s button to create a new job template."), "<i class=\"icon-plus\"></i> "),
        index: false,
        hover: true,

        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-lg-2 col-md-2 col-sm-4 col-xs-9',
                ngHref: '#/templates/{{template.type}}/{{template.id}}',
                awToolTip: '{{template.description | sanitize}}',
                dataPlacement: 'top'
            },
            type: {
                label: i18n._('Type'),
                ngBind: 'template.type_label',
                columnClass: 'col-lg-2 col-md-2 col-sm-4 hidden-xs'
            },
            smart_status: {
              label: i18n._('Activity'),
              columnClass: 'List-tableCell col-lg-2 col-md-3 hidden-sm hidden-xs',
              nosort: true,
              ngInclude: "'/static/partials/job-template-smart-status.html'",
              type: 'template'
            },
            labels: {
                label: i18n._('Labels'),
                type: 'labels',
                nosort: true,
                showDelete: true,
                columnClass: 'List-tableCell col-lg-2 col-md-3 hidden-sm hidden-xs'
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                type: 'buttonDropdown',
                basePaths: ['templates'],
                awToolTip: i18n._('Create a new template'),
                actionClass: 'btn List-dropdownSuccess',
                buttonContent: '&#43; ' + i18n._('ADD'),
                options: [
                    {
                        optionContent: i18n._('Job Template'),
                        optionSref: 'templates.addJobTemplate',
                        ngShow: 'canAddJobTemplate'
                    },
                    {
                        optionContent: i18n._('Workflow Template'),
                        optionSref: 'templates.addWorkflowJobTemplate',
                        ngShow: 'canAddWorkflowJobTemplate'
                    }
                ],
                ngShow: 'canAddJobTemplate || canAddWorkflowJobTemplate'
            }
        },

        fieldActions: {

            columnClass: 'col-lg-2 col-md-3 col-sm-4 col-xs-3',

            submit: {
                label: i18n._('Launch'),
                mode: 'all',
                ngClick: 'submitJob(template)',
                awToolTip: i18n._('Start a job using this template'),
                dataPlacement: 'top',
                ngShow: 'template.summary_fields.user_capabilities.start'
            },
            schedule: {
                label: i18n._('Schedule'),
                mode: 'all',
                ngClick: 'scheduleJob(template)',
                awToolTip: i18n._('Schedule future job template runs'),
                dataPlacement: 'top',
            },
            copy: {
                label: i18n._('Copy'),
                ngClick: 'copyTemplate(template)',
                "class": 'btn-danger btn-xs',
                awToolTip: i18n._('Copy template'),
                dataPlacement: 'top',
                ngShow: 'template.summary_fields.user_capabilities.copy'
            },
            edit: {
                label: i18n._('Edit'),
                ngClick: "editJobTemplate(template)",
                awToolTip: i18n._('Edit template'),
                "class": 'btn-default btn-xs',
                dataPlacement: 'top',
                ngShow: 'template.summary_fields.user_capabilities.edit',
                editStateParams: ['job_template_id', 'workflow_job_template_id']
            },
            view: {
                label: i18n._('View'),
                ngClick: "editJobTemplate(template)",
                awToolTip: i18n._('View template'),
                "class": 'btn-default btn-xs',
                dataPlacement: 'top',
                ngShow: '!template.summary_fields.user_capabilities.edit'
            },
            "delete": {
                label: i18n._('Delete'),
                ngClick: "deleteJobTemplate(template)",
                "class": 'btn-danger btn-xs',
                awToolTip: i18n._('Delete template'),
                dataPlacement: 'top',
                ngShow: 'template.summary_fields.user_capabilities.delete'
            }
        }
    };}];
