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

export default
    angular.module('WorkflowFormDefinition', [])

        .value ('WorkflowFormObject', {

            addTitle: 'New Workflow',
            editTitle: '{{ name }}',
            name: 'workflow_job_template',
            base: 'workflow',
            basePath: 'workflow_job_templates',
            // the top-most node of generated state tree
            stateTree: 'templates',
            activeEditState: 'templates.editWorkflowJobTemplate',
            tabs: true,

            fields: {
                name: {
                    label: 'Name',
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    column: 1
                },
                description: {
                    label: 'Description',
                    type: 'text',
                    column: 1
                },
                organization: {
                    label: 'Organization',
                    type: 'lookup',
                    sourceModel: 'organization',
                    basePath: 'organizations',
                    list: 'OrganizationList',
                    sourceField: 'name',
                    dataTitle: 'Organization',
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    column: 1
                },
                labels: {
                    label: 'Labels',
                    type: 'select',
                    class: 'Form-formGroup--fullWidth',
                    ngOptions: 'label.label for label in labelOptions track by label.value',
                    multiSelect: true,
                    dataTitle: 'Labels',
                    dataPlacement: 'right',
                    awPopOver: "<p>Optional labels that describe this job template, such as 'dev' or 'test'. Labels can be used to group and filter job templates and completed jobs in the Tower display.</p>",
                    dataContainer: 'body'
                },
                variables: {
                    label: 'Extra Variables',
                    type: 'textarea',
                    class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                    rows: 6,
                    "default": "---",
                    column: 2,
                    awPopOver: "<p>Pass extra command line variables to the playbook. This is the <code>-e</code> or <code>--extra-vars</code> command line parameter " +
                        "for <code>ansible-playbook</code>. Provide key/value pairs using either YAML or JSON.</p>" +
                        "JSON:<br />\n" +
                        "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                        "YAML:<br />\n" +
                        "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n",
                    dataTitle: 'Extra Variables',
                    dataPlacement: 'right',
                    dataContainer: "body"
                }
            },

            buttons: { //for now always generates <button> tags
                cancel: {
                    ngClick: 'formCancel()'
                },
                save: {
                    ngClick: 'formSave()',    //$scope.function to call on click, optional
                    ngDisabled: "workflow_form.$invalid || can_edit!==true"//true          //Disable when $pristine or $invalid, optional and when can_edit = false, for permission reasons
                }
            },

            related: {
                permissions: {
                    awToolTip: 'Please save before assigning permissions',
                    dataPlacement: 'top',
                    basePath: 'job_templates/:id/access_list/',
                    type: 'collection',
                    title: 'Permissions',
                    iterator: 'permission',
                    index: false,
                    open: false,
                    searchType: 'select',
                    actions: {
                        add: {
                            ngClick: "addPermission",
                            label: 'Add',
                            awToolTip: 'Add a permission',
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; ADD',
                            ngShow: '(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                        }
                    },

                    fields: {
                        username: {
                            key: true,
                            label: 'User',
                            linkBase: 'users',
                            class: 'col-lg-3 col-md-3 col-sm-3 col-xs-4'
                        },
                        role: {
                            label: 'Role',
                            type: 'role',
                            noSort: true,
                            class: 'col-lg-4 col-md-4 col-sm-4 col-xs-4',
                            searchable: false
                        },
                        team_roles: {
                            label: 'Team Roles',
                            type: 'team_roles',
                            noSort: true,
                            class: 'col-lg-5 col-md-5 col-sm-5 col-xs-4',
                            searchable: false
                        }
                    }
                },
                "notifications": {
                    include: "NotificationsList"
                }
            },

            relatedButtons: {
                add_survey: {
                    ngClick: 'addSurvey()',
                    ngShow: '!survey_exists',
                    awFeature: 'surveys',
                    awToolTip: 'Please save before adding a survey',
                    dataPlacement: 'top',
                    label: 'Add Survey',
                    class: 'Form-primaryButton'
                },
                edit_survey: {
                    ngClick: 'editSurvey()',
                    awFeature: 'surveys',
                    ngShow: 'survey_exists',
                    label: 'Edit Survey',
                    class: 'Form-primaryButton'
                },
                workflow_editor: {
                    ngClick: 'openWorkflowMaker()',
                    awToolTip: 'Please save before defining the workflow graph',
                    dataPlacement: 'top',
                    label: 'Workflow Editor',
                    class: 'Form-primaryButton'
                }
            },

            relatedSets: function(urls) {
                return {
                    permissions: {
                        iterator: 'permission',
                        url: urls.access_list
                    },
                    notifications: {
                        iterator: 'notification',
                        url: '/api/v1/notification_templates/'
                    }
                };
            }
        })

        .factory('WorkflowForm', ['WorkflowFormObject', 'NotificationsList',
        function(WorkflowFormObject, NotificationsList) {
            return function() {
                var itm;

                for (itm in WorkflowFormObject.related) {
                    if (WorkflowFormObject.related[itm].include === "NotificationsList") {
                        WorkflowFormObject.related[itm] = NotificationsList;
                        WorkflowFormObject.related[itm].generateList = true;   // tell form generator to call list generator and inject a list
                    }
                }

                return WorkflowFormObject;
            };
        }]);
