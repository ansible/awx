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
    angular.module('JobTemplateFormDefinition', [ 'CompletedJobsDefinition'])

        .factory('JobTemplateFormObject', ['i18n', function(i18n) {
        return {

            addTitle: i18n._('New Job Template'),
            editTitle: '{{ name }}',
            name: 'job_template',
            basePath: 'job_templates',
            // the top-most node of generated state tree
            stateTree: 'jobTemplates',
            tabs: true,
            // (optional) array of supporting templates to ng-include inside generated html
            include: ['/static/partials/survey-maker-modal.html'],

            fields: {
                name: {
                    label: i18n._('Name'),
                    type: 'text',
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)',
                    required: true,
                    column: 1
                },
                description: {
                    label: i18n._('Description'),
                    type: 'text',
                    column: 1,
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                job_type: {
                    label: i18n._('Job Type'),
                    type: 'select',
                    ngOptions: 'type.label for type in job_type_options track by type.value',
                    ngChange: 'jobTypeChange()',
                    "default": 0,
                    required: true,
                    column: 1,
                    awPopOver: i18n._("<p>When this template is submitted as a job, setting the type to <em>run</em> will execute the playbook, running tasks " +
                        " on the selected hosts.</p> <p>Setting the type to <em>check</em> will not execute the playbook. Instead, <code>ansible</code> will check playbook " +
                        " syntax, test environment setup and report problems.</p> <p>Setting the type to <em>scan</em> will execute the playbook and store any " +
                        " scanned facts for use with Tower's System Tracking feature.</p>"),
                    dataTitle: i18n._('Job Type'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_job_type_on_launch',
                        ngShow: "!job_type.value || job_type.value !== 'scan'",
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                inventory: {
                    label: i18n._('Inventory'),
                    type: 'lookup',
                    basePath: 'inventory',
                    list: 'InventoryList',
                    sourceModel: 'inventory',
                    sourceField: 'name',
                    awRequiredWhen: {
                        reqExpression: '!ask_inventory_on_launch',
                        alwaysShowAsterisk: true
                    },
                    requiredErrorMsg: "Please select an Inventory or check the Prompt on launch option.",
                    column: 1,
                    awPopOver: i18n._("<p>Select the inventory containing the hosts you want this job to manage.</p>"),
                    dataTitle: i18n._('Inventory'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_inventory_on_launch',
                        ngShow: "!job_type.value || job_type.value !== 'scan'",
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                project: {
                    label: i18n._('Project'),
                    labelAction: {
                        label: 'RESET',
                        ngClick: 'resetProjectToDefault()',
                        'class': "{{!(job_type.value === 'scan' && project_name !== 'Default') ? 'hidden' : ''}}",
                    },
                    type: 'lookup',
                    list: 'ProjectList',
                    basePath: 'projects',
                    sourceModel: 'project',
                    sourceField: 'name',
                    awRequiredWhen: {
                        reqExpression: "projectrequired",
                        init: "true"
                    },
                    column: 1,
                    awPopOver: i18n._("<p>Select the project containing the playbook you want this job to execute.</p>"),
                    dataTitle: i18n._('Project'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                playbook: {
                    label: i18n._('Playbook'),
                    type:'select',
                    ngOptions: 'book for book in playbook_options track by book',
                    ngDisabled: "(job_type.value === 'scan' && project_name === 'Default') || !(job_template_obj.summary_fields.user_capabilities.edit || canAdd)",
                    id: 'playbook-select',
                    awRequiredWhen: {
                        reqExpression: "playbookrequired",
                        init: "true"
                    },
                    column: 1,
                    awPopOver: i18n._("<p>Select the playbook to be executed by this job.</p>"),
                    dataTitle: i18n._('Playbook'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    includePlaybookNotFoundError: true
                },
                credential: {
                    label: i18n._('Machine Credential'),
                    type: 'lookup',
                    list: 'CredentialList',
                    basePath: 'credentials',
                    search: {
                        kind: 'ssh'
                    },
                    sourceModel: 'credential',
                    sourceField: 'name',
                    awRequiredWhen: {
                        reqExpression: '!ask_credential_on_launch',
                        alwaysShowAsterisk: true
                    },
                    requiredErrorMsg: "Please select a Machine Credential or check the Prompt on launch option.",
                    column: 1,
                    awPopOver: i18n._("<p>Select the credential you want the job to use when accessing the remote hosts. Choose the credential containing " +
                     " the username and SSH key or password that Ansible will need to log into the remote hosts.</p>"),
                    dataTitle: i18n._('Credential'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_credential_on_launch',
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                cloud_credential: {
                    label: i18n._('Cloud Credential'),
                    type: 'lookup',
                    list: 'CredentialList',
                    basePath: 'credentials',
                    search: {
                        cloud: 'true'
                    },
                    sourceModel: 'cloud_credential',
                    sourceField: 'name',
                    column: 1,
                    awPopOver: i18n._("<p>Selecting an optional cloud credential in the job template will pass along the access credentials to the " +
                        "running playbook, allowing provisioning into the cloud without manually passing parameters to the included modules.</p>"),
                    dataTitle: i18n._('Cloud Credential'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                network_credential: {
                    label: i18n._('Network Credential'),
                    type: 'lookup',
                    list: 'CredentialList',
                    basePath: 'credentials',
                    search: {
                        kind: 'net'
                    },
                    sourceModel: 'network_credential',
                    sourceField: 'name',
                    column: 1,
                    awPopOver: i18n._("<p>Network credentials are used by Ansible networking modules to connect to and manage networking devices.</p>"),
                    dataTitle: i18n._('Network Credential'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                forks: {
                    label: i18n._('Forks'),
                    id: 'forks-number',
                    type: 'number',
                    integer: true,
                    min: 0,
                    spinner: true,
                    "default": '0',
                    'class': "input-small",
                    column: 1,
                    awPopOver: i18n._('<p>The number of parallel or simultaneous processes to use while executing the playbook. 0 signifies ' +
                        'the default value from the <a id="ansible_forks_docs" href=\"http://docs.ansible.com/intro_configuration.html#the-ansible-configuration-file\" ' +
                        ' target=\"_blank\">ansible configuration file</a>.</p>'),
                    dataTitle: i18n._('Forks'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)' // TODO: get working
                },
                limit: {
                    label: i18n._('Limit'),
                    type: 'text',
                    column: 1,
                    awPopOver: i18n._("<p>Provide a host pattern to further constrain the list of hosts that will be managed or affected by the playbook. " +
                        "Multiple patterns can be separated by &#59; &#58; or &#44;</p><p>For more information and examples see " +
                        "<a href=\"http://docs.ansible.com/intro_patterns.html\" target=\"_blank\">the Patterns topic at docs.ansible.com</a>.</p>"),
                    dataTitle: i18n._('Limit'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_limit_on_launch',
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                verbosity: {
                    label: i18n._('Verbosity'),
                    type: 'select',
                    ngOptions: 'v.label for v in verbosity_options track by v.value',
                    "default": 1,
                    required: true,
                    column: 1,
                    awPopOver: i18n._("<p>Control the level of output ansible will produce as the playbook executes.</p>"),
                    dataTitle: i18n._('Verbosity'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                job_tags: {
                    label: i18n._('Job Tags'),
                    type: 'textarea',
                    rows: 5,
                    'elementClass': 'Form-textInput',
                    column: 2,
                    awPopOver: i18n._("<p>Provide a comma separated list of tags.</p>\n" +
                        "<p>Tags are useful when you have a large playbook, and you want to run a specific part of a play or task.</p>" +
                        "<p>Consult the Ansible documentation for further details on the usage of tags.</p>"),
                    dataTitle: i18n._("Job Tags"),
                    dataPlacement: "right",
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_tags_on_launch',
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                skip_tags: {
                    label: i18n._('Skip Tags'),
                    type: 'textarea',
                    rows: 5,
                    'elementClass': 'Form-textInput',
                    column: 2,
                    awPopOver: i18n._("<p>Provide a comma separated list of tags.</p>\n" +
                        "<p>Skip tags are useful when you have a large playbook, and you want to skip specific parts of a play or task.</p>" +
                        "<p>Consult the Ansible documentation for further details on the usage of tags.</p>"),
                    dataTitle: i18n._("Skip Tags"),
                    dataPlacement: "right",
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_skip_tags_on_launch',
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                checkbox_group: {
                    label: i18n._('Options'),
                    type: 'checkbox_group',
                    fields: [{
                        name: 'become_enabled',
                        label: i18n._('Enable Privilege Escalation'),
                        type: 'checkbox',
                        column: 2,
                        awPopOver: i18n._("<p>If enabled, run this playbook as an administrator. This is the equivalent of passing the <code>--become</code> option to the <code>ansible-playbook</code> command. </p>"),
                        dataPlacement: 'right',
                        dataTitle: i18n._('Become Privilege Escalation'),
                        dataContainer: "body",
                        labelClass: 'stack-inline',
                        ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                    }, {
                        name: 'allow_callbacks',
                        label: i18n._('Allow Provisioning Callbacks'),
                        type: 'checkbox',
                        ngChange: "toggleCallback('host_config_key')",
                        column: 2,
                        awPopOver: i18n._("<p>Enables creation of a provisioning callback URL. Using the URL a host can contact Tower and request a configuration update " +
                            "using this job template.</p>"),
                        dataPlacement: 'right',
                        dataTitle: i18n._('Allow Provisioning Callbacks'),
                        dataContainer: "body",
                        labelClass: 'stack-inline',
                        ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                    }]
                },
                callback_url: {
                    label: i18n._('Provisioning Callback URL'),
                    type: 'text',
                    readonly: true,
                    ngShow: "allow_callbacks && allow_callbacks !== 'false'",
                    column: 2,
                    awPopOver: "callback_help",
                    awPopOverWatch: "callback_help",
                    dataPlacement: 'top',
                    dataTitle: i18n._('Provisioning Callback URL'),
                    dataContainer: "body",
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                host_config_key: {
                    label: i18n._('Host Config Key'),
                    type: 'text',
                    ngShow: "allow_callbacks  && allow_callbacks !== 'false'",
                    ngChange: "configKeyChange()",
                    genMD5: true,
                    column: 2,
                    awPopOver: "callback_help",
                    awPopOverWatch: "callback_help",
                    dataPlacement: 'right',
                    dataTitle: i18n._("Host Config Key"),
                    dataContainer: "body",
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                labels: {
                    label: i18n._('Labels'),
                    type: 'select',
                    class: 'Form-formGroup--fullWidth',
                    ngOptions: 'label.label for label in labelOptions track by label.value',
                    multiSelect: true,
                    dataTitle: i18n._('Labels'),
                    dataPlacement: 'right',
                    awPopOver: i18n._("<p>Optional labels that describe this job template, such as 'dev' or 'test'. Labels can be used to group and filter job templates and completed jobs in the Tower display.</p>"),
                    dataContainer: 'body',
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                variables: {
                    label: i18n._('Extra Variables'),
                    type: 'textarea',
                    class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                    rows: 6,
                    "default": "---",
                    column: 2,
                    awPopOver: i18n._("<p>Pass extra command line variables to the playbook. This is the <code>-e</code> or <code>--extra-vars</code> command line parameter " +
                        "for <code>ansible-playbook</code>. Provide key/value pairs using either YAML or JSON.</p>" +
                        "JSON:<br />\n" +
                        "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                        "YAML:<br />\n" +
                        "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n"),
                    dataTitle: i18n._('Extra Variables'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_variables_on_launch',
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)' // TODO: get working
                }
            },

            buttons: { //for now always generates <button> tags
                add_survey: {
                    ngClick: 'addSurvey()',
                    ngShow: 'job_type.value !== "scan" && !survey_exists && (job_template_obj.summary_fields.user_capabilities.edit || canAdd)',
                    awFeature: 'surveys',
                    awToolTip: 'Surveys allow users to be prompted at job launch with a series of questions related to the job. This allows for variables to be defined that affect the playbook run at time of launch.',
                    dataPlacement: 'top'
                },
                edit_survey: {
                    ngClick: 'editSurvey()',
                    awFeature: 'surveys',
                    ngShow: 'job_type.value !== "scan" && survey_exists && (job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                view_survey: {
                    ngClick: 'editSurvey()',
                    awFeature: 'surveys',
                    ngShow: 'job_type.value !== "scan" && survey_exists && !(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                cancel: {
                    ngClick: 'formCancel()',
                    ngShow: '(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                close: {
                    ngClick: 'formCancel()',
                    ngShow: '!(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                save: {
                    ngClick: 'formSave()',    //$scope.function to call on click, optional
                    ngDisabled: "job_templates_form.$invalid",//true          //Disable when $pristine or $invalid, optional and when can_edit = false, for permission reasons
                    ngShow: '(job_template_obj.summary_fields.user_capabilities.edit || canAdd)'
                }
            },

            related: {
                "completed_jobs": {
                    include: "CompletedJobsList"
                },
                permissions: {
                    awToolTip: i18n._('Please save before assigning permissions'),
                    dataPlacement: 'top',
                    basePath: 'api/v1/job_templates/{{$stateParams.job_template_id}}/access_list/',
                    search: {
                        order_by: 'username'
                    },
                    type: 'collection',
                    title: i18n._('Permissions'),
                    iterator: 'permission',
                    index: false,
                    open: false,
                    actions: {
                        add: {
                            ngClick: "$state.go('.add')",
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
                        },
                        team_roles: {
                            label: 'Team Roles',
                            type: 'team_roles',
                            noSort: true,
                            class: 'col-lg-5 col-md-5 col-sm-5 col-xs-4',
                        }
                    }
                },
                "notifications": {
                    include: "NotificationsList"
                }
            },

            relatedSets: function(urls) {
                return {
                    completed_jobs: {
                        iterator: 'completed_job',
                        url: urls.jobs + '?or__status=successful&or__status=failed&or__status=error&or__status=canceled'
                    },
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
        };}])

        .factory('JobTemplateForm', ['JobTemplateFormObject', 'NotificationsList', 'CompletedJobsList',
        function(JobTemplateFormObject, NotificationsList, CompletedJobsList) {
            return function() {
                var itm;

                for (itm in JobTemplateFormObject.related) {
                    if (JobTemplateFormObject.related[itm].include === "NotificationsList") {
                        JobTemplateFormObject.related[itm] = NotificationsList;
                        JobTemplateFormObject.related[itm].generateList = true;   // tell form generator to call list generator and inject a list
                    }
                    if (JobTemplateFormObject.related[itm].include === "CompletedJobsList") {
                        JobTemplateFormObject.related[itm] = CompletedJobsList;
                        JobTemplateFormObject.related[itm].generateList = true;
                    }
                }

                return JobTemplateFormObject;
            };
        }]);
