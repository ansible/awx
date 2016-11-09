/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name forms.function:JobTemplate
 * @description This form is for adding/editing a Job Template
*/

export default
    angular.module('WorkflowMakerFormDefinition', [])

        .value ('WorkflowMakerFormObject', {

            addTitle: '',
            editTitle: '',
            name: 'workflow_maker',
            basePath: 'job_templates',
            tabs: false,
            cancelButton: false,
            showHeader: false,

            fields: {
                edgeType: {
                    label: 'Type',
                    type: 'radio_group',
                    ngShow: 'selectedTemplate && showTypeOptions',
                    options: [
                        {
                            label: 'On&nbsp;Success',
                            value: 'success',
                            ngShow: '!edgeTypeRestriction || edgeTypeRestriction === "successFailure"'
                        },
                        {
                            label: 'On&nbsp;Failure',
                            value: 'failure',
                            ngShow: '!edgeTypeRestriction || edgeTypeRestriction === "successFailure"'
                        },
                        {
                            label: 'Always',
                            value: 'always',
                            ngShow: '!edgeTypeRestriction || edgeTypeRestriction === "always"'
                        }
                    ],
                    awRequiredWhen: {
                        reqExpression: 'showTypeOptions'
                    }
                },
                credential: {
                    label: 'Credential',
                    type: 'lookup',
                    sourceModel: 'credential',
                    sourceField: 'name',
                    ngClick: 'lookUpCredential()',
                    requiredErrorMsg: "Please select a Credential.",
                    column: 1,
                    class: 'Form-formGroup--fullWidth',
                    awPopOver: "<p>Select the credential you want the job to use when accessing the remote hosts. Choose the credential containing " +
                     " the username and SSH key or password that Ansible will need to log into the remote hosts.</p>",
                    dataTitle: 'Credential',
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngShow: "selectedTemplate.ask_credential_on_launch",
                    awRequiredWhen: {
                        reqExpression: 'selectedTemplate.ask_credential_on_launch'
                    }
                },
                inventory: {
                    label: 'Inventory',
                    type: 'lookup',
                    sourceModel: 'inventory',
                    sourceField: 'name',
                    list: 'OrganizationList',
                    basePath: 'organization',
                    ngClick: 'lookUpInventory()',
                    requiredErrorMsg: "Please select an Inventory.",
                    column: 1,
                    class: 'Form-formGroup--fullWidth',
                    awPopOver: "<p>Select the inventory containing the hosts you want this job to manage.</p>",
                    dataTitle: 'Inventory',
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngShow: "selectedTemplate.ask_inventory_on_launch",
                    awRequiredWhen: {
                        reqExpression: 'selectedTemplate.ask_inventory_on_launch'
                    }
                },
                job_type: {
                    label: 'Job Type',
                    type: 'select',
                    ngOptions: 'type.label for type in job_type_options track by type.value',
                    "default": 0,
                    column: 1,
                    class: 'Form-formGroup--fullWidth',
                    awPopOver: "<p>When this template is submitted as a job, setting the type to <em>run</em> will execute the playbook, running tasks " +
                        " on the selected hosts.</p> <p>Setting the type to <em>check</em> will not execute the playbook. Instead, <code>ansible</code> will check playbook " +
                        " syntax, test environment setup and report problems.</p> <p>Setting the type to <em>scan</em> will execute the playbook and store any " +
                        " scanned facts for use with Tower's System Tracking feature.</p>",
                    dataTitle: 'Job Type',
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngShow: "selectedTemplate.ask_job_type_on_launch",
                    awRequiredWhen: {
                        reqExpression: 'selectedTemplate.ask_job_type_on_launch'
                    }
                },
                limit: {
                    label: 'Limit',
                    type: 'text',
                    addRequired: false,
                    editRequired: false,
                    column: 1,
                    class: 'Form-formGroup--fullWidth',
                    awPopOver: "<p>Provide a host pattern to further constrain the list of hosts that will be managed or affected by the playbook. " +
                        "Multiple patterns can be separated by &#59; &#58; or &#44;</p><p>For more information and examples see " +
                        "<a href=\"http://docs.ansible.com/intro_patterns.html\" target=\"_blank\">the Patterns topic at docs.ansible.com</a>.</p>",
                    dataTitle: 'Limit',
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngShow: "selectedTemplate.ask_limit_on_launch"
                },
                job_tags: {
                    label: 'Job Tags',
                    type: 'textarea',
                    rows: 5,
                    addRequired: false,
                    editRequired: false,
                    'elementClass': 'Form-textInput',
                    column: 2,
                    class: 'Form-formGroup--fullWidth',
                    awPopOver: "<p>Provide a comma separated list of tags.</p>\n" +
                        "<p>Tags are useful when you have a large playbook, and you want to run a specific part of a play or task.</p>" +
                        "<p>Consult the Ansible documentation for further details on the usage of tags.</p>",
                    dataTitle: "Job Tags",
                    dataPlacement: "right",
                    dataContainer: "body",
                    ngShow: "selectedTemplate.ask_tags_on_launch"
                },
                skip_tags: {
                    label: 'Skip Tags',
                    type: 'textarea',
                    rows: 5,
                    addRequired: false,
                    editRequired: false,
                    'elementClass': 'Form-textInput',
                    column: 2,
                    class: 'Form-formGroup--fullWidth',
                    awPopOver: "<p>Provide a comma separated list of tags.</p>\n" +
                        "<p>Skip tags are useful when you have a large playbook, and you want to skip specific parts of a play or task.</p>" +
                        "<p>Consult the Ansible documentation for further details on the usage of tags.</p>",
                    dataTitle: "Skip Tags",
                    dataPlacement: "right",
                    dataContainer: "body",
                    ngShow: "selectedTemplate.ask_skip_tags_on_launch"
                }
            },
            buttons: {
                cancel: {
                    ngClick: 'cancelNodeForm()'
                },
                save: {
                    ngClick: 'saveNodeForm()',
                    ngDisabled: "workflow_maker_form.$invalid || !selectedTemplate"
                }
            }
        })
        .factory('WorkflowMakerForm', ['WorkflowMakerFormObject', 'NotificationsList', function(WorkflowMakerFormObject, NotificationsList) {
            return function() {
                var itm;
                for (itm in WorkflowMakerFormObject.related) {
                    if (WorkflowMakerFormObject.related[itm].include === "NotificationsList") {
                        WorkflowMakerFormObject.related[itm] = NotificationsList;
                        WorkflowMakerFormObject.related[itm].generateList = true;   // tell form generator to call list generator and inject a list
                    }
                }
                return WorkflowMakerFormObject;
            };
        }]);
