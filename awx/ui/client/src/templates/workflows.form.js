/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name forms.function:Workflow
 * @description This form is for adding/editing a Workflow
*/

export default ['NotificationsList', 'i18n', function(NotificationsList, i18n) {
    return function() {
        var WorkflowFormObject = {

            addTitle: i18n._('NEW WORKFLOW JOB TEMPLATE'),
            editTitle: '{{ name }}',
            name: 'workflow_job_template',
            breadcrumbName: i18n._('WORKFLOW'),
            base: 'workflow',
            basePath: 'workflow_job_templates',
            // the top-most node of generated state tree
            stateTree: 'templates',
            activeEditState: 'templates.editWorkflowJobTemplate',
            tabs: true,
            detailsClick: "$state.go('templates.editWorkflowJobTemplate')",
            include: ['/static/partials/survey-maker-modal.html'],

            fields: {
                name: {
                    label: i18n._('Name'),
                    type: 'text',
                    required: true,
                    ngDisabled: '!(workflow_job_template_obj.summary_fields.user_capabilities.edit || canAddWorkflowJobTemplate)',
                    column: 1
                },
                description: {
                    label: i18n._('Description'),
                    type: 'text',
                    column: 1,
                    ngDisabled: '!(workflow_job_template_obj.summary_fields.user_capabilities.edit || canAddWorkflowJobTemplate)'
                },
                organization: {
                    label: i18n._('Organization'),
                    type: 'lookup',
                    sourceModel: 'organization',
                    basePath: 'organizations',
                    list: 'OrganizationList',
                    sourceField: 'name',
                    dataTitle: i18n._('Organization'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    awRequiredWhen: {
                        reqExpression: '!current_user.is_superuser'
                    },
                    column: 1,
                    ngDisabled: '!(workflow_job_template_obj.summary_fields.user_capabilities.edit || canAddWorkflowJobTemplate) || !canEditOrg',
                    awLookupWhen: '(workflow_job_template_obj.summary_fields.user_capabilities.edit || canAddWorkflowJobTemplate) && canEditOrg'
                },
                labels: {
                    label: i18n._('Labels'),
                    type: 'select',
                    class: 'Form-formGroup--fullWidth',
                    ngOptions: 'label.label for label in labelOptions track by label.value',
                    multiSelect: true,
                    dataTitle: i18n._('Labels'),
                    dataPlacement: 'right',
                    awPopOver: "<p>" + i18n._("Optional labels that describe this job template, such as 'dev' or 'test'. Labels can be used to group and filter job templates and completed jobs.") + "</p>",
                    dataContainer: 'body',
                    ngDisabled: '!(workflow_job_template_obj.summary_fields.user_capabilities.edit || canAddWorkflowJobTemplate)'
                },
                variables: {
                    label: i18n._('Extra Variables'),
                    type: 'textarea',
                    class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                    rows: 6,
                    "default": "---",
                    column: 2,
                    awPopOver:i18n._('Pass extra command line variables to the playbook. This is the -e or --extra-vars command line parameter for ansible-playbook. Provide key/value pairs using either YAML or JSON. Refer to the Ansible Tower documentaton for example syntax.'),
                    dataTitle: i18n._('Extra Variables'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngDisabled: '!(workflow_job_template_obj.summary_fields.user_capabilities.edit || canAddWorkflowJobTemplate)' // TODO: get working
                }
            },

            buttons: { //for now always generates <button> tags
                cancel: {
                    ngClick: 'formCancel()',
                    ngShow: '(workflow_job_template_obj.summary_fields.user_capabilities.edit || canAddWorkflowJobTemplate)'
                },
                close: {
                    ngClick: 'formCancel()',
                    ngShow: '!(workflow_job_template_obj.summary_fields.user_capabilities.edit || canAddWorkflowJobTemplate)'
                },
                save: {
                    ngClick: 'formSave()',    //$scope.function to call on click, optional
                    ngDisabled: "workflow_job_template_form.$invalid || can_edit!==true", //Disable when $pristine or $invalid, optional and when can_edit = false, for permission reasons
                    ngShow: '(workflow_job_template_obj.summary_fields.user_capabilities.edit || canAddWorkflowJobTemplate)'
                }
            },

            related: {
                permissions: {
                    name: 'permissions',
                    awToolTip: i18n._('Please save before assigning permissions.'),
                    dataPlacement: 'top',
                    basePath: 'api/v2/workflow_job_templates/{{$stateParams.workflow_job_template_id}}/access_list/',
                    search: {
                        order_by: 'username'
                    },
                    type: 'collection',
                    title: i18n._('Permissions'),
                    iterator: 'permission',
                    index: false,
                    open: false,
                    ngClick: "$state.go('templates.editWorkflowJobTemplate.permissions')",
                    actions: {
                        add: {
                            ngClick: "$state.go('.add')",
                            label: i18n._('Add'),
                            awToolTip: i18n._('Add a permission'),
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; '+ i18n._('ADD'),
                            ngShow: '(workflow_job_template_obj.summary_fields.user_capabilities.edit || canAddWorkflowJobTemplate)'
                        }
                    },

                    fields: {
                        username: {
                            key: true,
                            label: i18n._('User'),
                            linkBase: 'users',
                            class: 'col-lg-3 col-md-3 col-sm-3 col-xs-4'
                        },
                        role: {
                            label: i18n._('Role'),
                            type: 'role',
                            nosort: true,
                            class: 'col-lg-4 col-md-4 col-sm-4 col-xs-4',
                        },
                        team_roles: {
                            label: i18n._('Team Roles'),
                            type: 'team_roles',
                            nosort: true,
                            class: 'col-lg-5 col-md-5 col-sm-5 col-xs-4',
                        }
                    }
                },
                "notifications": {
                    include: "NotificationsList"
                }
            },

            relatedButtons: {
                view_survey: {
                    ngClick: 'editSurvey()',
                    awFeature: 'surveys',
                    ngShow: '($state.is(\'templates.addWorkflowJobTemplate\') || $state.is(\'templates.editWorkflowJobTemplate\')) && survey_exists && !(workflow_job_template_obj.summary_fields.user_capabilities.edit || canAddWorkflowJobTemplate)',
                    label: i18n._('View Survey'),
                    class: 'Form-primaryButton'
                },
                add_survey: {
                    ngClick: 'addSurvey()',
                    ngShow: '!survey_exists && ($state.includes(\'templates.addWorkflowJobTemplate\') || $state.includes(\'templates.editWorkflowJobTemplate\'))',
                    awFeature: 'surveys',
                    awToolTip: '{{surveyTooltip}}',
                    dataPlacement: 'top',
                    label: i18n._('Add Survey'),
                    class: 'Form-primaryButton'
                },
                edit_survey: {
                    ngClick: 'editSurvey()',
                    awFeature: 'surveys',
                    ngShow: 'survey_exists && ($state.includes(\'templates.addWorkflowJobTemplate\') || $state.includes(\'templates.editWorkflowJobTemplate\'))',
                    label: i18n._('Edit Survey'),
                    class: 'Form-primaryButton',
                    awToolTip: '{{surveyTooltip}}',
                    dataPlacement: 'top'
                },
                workflow_editor: {
                    ngClick: 'openWorkflowMaker()',
                    ngShow: '$state.includes(\'templates.addWorkflowJobTemplate\') || $state.includes(\'templates.editWorkflowJobTemplate\')',
                    awToolTip: '{{workflowEditorTooltip}}',
                    dataPlacement: 'top',
                    label: i18n._('Workflow Editor'),
                    class: 'Form-primaryButton'
                }
            }
        };

        var itm;

        for (itm in WorkflowFormObject.related) {
            if (WorkflowFormObject.related[itm].include === "NotificationsList") {
                WorkflowFormObject.related[itm] = _.clone(NotificationsList);
                WorkflowFormObject.related[itm].ngClick = "$state.go('templates.editWorkflowJobTemplate.notifications')";
                WorkflowFormObject.related[itm].generateList = true;   // tell form generator to call list generator and inject a list
            }
        }

        return WorkflowFormObject;
    };
}];
