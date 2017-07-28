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


export default ['NotificationsList', 'CompletedJobsList', 'i18n',
function(NotificationsList, CompletedJobsList, i18n) {
    return function() {
        var JobTemplateFormObject = {

            addTitle: i18n._('NEW JOB TEMPLATE'),
            editTitle: '{{ name }}',
            name: 'job_template',
            breadcrumbName: i18n._('JOB TEMPLATE'),
            basePath: 'job_templates',
            // the top-most node of generated state tree
            stateTree: 'templates',
            tabs: true,
            activeEditState: 'templates.editJobTemplate',
            // (optional) array of supporting templates to ng-include inside generated html
            include: ['/static/partials/survey-maker-modal.html'],
            detailsClick: "$state.go('templates.editJobTemplate')",

            fields: {
                name: {
                    label: i18n._('Name'),
                    type: 'text',
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)',
                    required: true,
                    column: 1
                },
                description: {
                    label: i18n._('Description'),
                    type: 'text',
                    column: 1,
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                job_type: {
                    label: i18n._('Job Type'),
                    type: 'select',
                    ngOptions: 'type.label for type in job_type_options track by type.value',
                    ngChange: 'jobTypeChange()',
                    "default": 0,
                    required: true,
                    column: 1,
                    awPopOver: "<p>" + i18n.sprintf(i18n._("When this template is submitted as a job, setting the type to %s will execute the playbook, running tasks " +
                        " on the selected hosts."), "<em>run</em>") + "</p> <p>" +
                        i18n.sprintf(i18n._("Setting the type to %s will not execute the playbook."), "<em>check</em>") + " " +
                        i18n.sprintf(i18n._("Instead, %s will check playbook " +
                        " syntax, test environment setup and report problems."), "<code>ansible</code>") + "</p>",
                    dataTitle: i18n._('Job Type'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_job_type_on_launch',
                        text: i18n._('Prompt on launch'),
                        ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                inventory: {
                    label: i18n._('Inventory'),
                    type: 'lookup',
                    basePath: 'inventory',
                    list: 'InventoryList',
                    sourceModel: 'inventory',
                    sourceField: 'name',
                    autopopulateLookup: false,
                    awRequiredWhen: {
                        reqExpression: '!ask_inventory_on_launch',
                        alwaysShowAsterisk: true
                    },
                    requiredErrorMsg: i18n._("Please select an Inventory or check the Prompt on launch option."),
                    column: 1,
                    awPopOver: "<p>" + i18n._("Select the inventory containing the hosts you want this job to manage.") + "</p>",
                    dataTitle: i18n._('Inventory'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_inventory_on_launch',
                        ngChange: 'job_template_form.inventory_name.$validate()',
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                project: {
                    label: i18n._('Project'),
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
                    awPopOver: "<p>" + i18n._("Select the project containing the playbook you want this job to execute.") + "</p>",
                    dataTitle: i18n._('Project'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                playbook: {
                    label: i18n._('Playbook'),
                    type:'select',
                    ngOptions: 'book for book in playbook_options track by book',
                    ngDisabled: "!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate) || disablePlaybookBecausePermissionDenied",
                    id: 'playbook-select',
                    awRequiredWhen: {
                        reqExpression: "playbookrequired",
                        init: "true"
                    },
                    column: 1,
                    awPopOver: "<p>" + i18n._("Select the playbook to be executed by this job.") + "</p>",
                    dataTitle: i18n._('Playbook'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    includePlaybookNotFoundError: true
                },
                credential: {
                    label: i18n._('Credential'),
                    type: 'custom',
                    control: `
                        <multi-credential
                            credentials="credentials"
                            prompt="ask_credential_on_launch"
                            selected-credentials="selectedCredentials"
                            credential-not-present="credentialNotPresent"
                            credentials-to-post="credentialsToPost"
                            field-is-disabled="!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)">
                        </multi-credential>`,
                    required: true,
                    awPopOver: "<p>" + i18n._("Select credentials that allow {{BRAND_NAME}} to access the nodes this job will be ran against. You can only select one credential of each type.<br /><br />You must select either a machine (SSH) credential or \"Prompt on launch\".  \"Prompt on launch\" requires you to select a machine credential at run time.<br /><br />If you select credentials AND check the \"Prompt on launch\" box, you make the selected credentials the defaults that can be updated at run time.") + "</p>",
                    dataTitle: i18n._('Credentials'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_credential_on_launch',
                        text: i18n._('Prompt on launch'),
                        ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                    }
                },
                forks: {
                    label: i18n._('Forks'),
                    id: 'forks-number',
                    type: 'number',
                    integer: true,
                    min: 1,
                    spinner: true,
                    'class': "input-small",
                    column: 1,
                    awPopOver: '<p>' + i18n.sprintf(i18n._('The number of parallel or simultaneous processes to use while executing the playbook. Inputting no value will use ' +
                        'the default value from the %sansible configuration file%s.'), '' +
                        '<a id="ansible_forks_docs" href=\"http://docs.ansible.com/intro_configuration.html#the-ansible-configuration-file\" ' +
                        ' target=\"_blank\">', '</a>') +'</p>',
                    placeholder: 'DEFAULT',
                    dataTitle: i18n._('Forks'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                limit: {
                    label: i18n._('Limit'),
                    type: 'text',
                    column: 1,
                    awPopOver: "<p>" + i18n.sprintf(i18n._("Provide a host pattern to further constrain the list of hosts that will be managed or affected by the playbook. " +
                        "Multiple patterns can be separated by %s %s or %s"), "&#59;", "&#58;", "&#44;") + "</p><p>" +
                        i18n.sprintf(i18n._("For more information and examples see " +
                        "%sthe Patterns topic at docs.ansible.com%s."), "<a href=\"http://docs.ansible.com/intro_patterns.html\" target=\"_blank\">", "</a>") + "</p>",
                    dataTitle: i18n._('Limit'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_limit_on_launch',
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                verbosity: {
                    label: i18n._('Verbosity'),
                    type: 'select',
                    ngOptions: 'v.label for v in verbosity_options track by v.value',
                    "default": 1,
                    required: true,
                    column: 1,
                    awPopOver: "<p>" + i18n._("Control the level of output ansible will produce as the playbook executes.") + "</p>",
                    dataTitle: i18n._('Verbosity'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_verbosity_on_launch',
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)',
                },
                instance_groups: {
                    label: i18n._('Instance Groups'),
                    type: 'custom',
                    awPopOver: "<p>" + i18n._("Select the Instance Groups for this Job Template to run on.") + "</p>",
                    dataTitle: i18n._('Instance Groups'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    control: '<instance-groups-multiselect instance-groups="instance_groups" field-is-disabled="!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)"></instance-groups-multiselect>',
                },
                job_tags: {
                    label: i18n._('Job Tags'),
                    type: 'select',
                    multiSelect: true,
                    'elementClass': 'Form-textInput',
                    ngOptions: 'tag.label for tag in job_tag_options track by tag.value',
                    column: 2,
                    awPopOver: "<p>" + i18n._("Provide a comma separated list of tags.") + "</p>\n" +
                        "<p>" + i18n._("Tags are useful when you have a large playbook, and you want to run a specific part of a play or task.") + "</p>" +
                        "<p>" + i18n._("Consult the Ansible documentation for further details on the usage of tags.") + "</p>",
                    dataTitle: i18n._("Job Tags"),
                    dataPlacement: "right",
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_tags_on_launch',
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                skip_tags: {
                    label: i18n._('Skip Tags'),
                    type: 'select',
                    multiSelect: true,
                    'elementClass': 'Form-textInput',
                    ngOptions: 'tag.label for tag in skip_tag_options track by tag.value',
                    column: 2,
                    awPopOver: "<p>" + i18n._("Provide a comma separated list of tags.") + "</p>\n" +
                        "<p>" + i18n._("Skip tags are useful when you have a large playbook, and you want to skip specific parts of a play or task.") + "</p>" +
                        "<p>" + i18n._("Consult the Ansible documentation for further details on the usage of tags.") + "</p>",
                    dataTitle: i18n._("Skip Tags"),
                    dataPlacement: "right",
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_skip_tags_on_launch',
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                labels: {
                    label: i18n._('Labels'),
                    type: 'select',
                    ngOptions: 'label.label for label in labelOptions track by label.value',
                    multiSelect: true,
                    dataTitle: i18n._('Labels'),
                    dataPlacement: 'right',
                    awPopOver: "<p>" + i18n._("Optional labels that describe this job template, such as 'dev' or 'test'. Labels can be used to group and filter job templates and completed jobs.") + "</p>",
                    dataContainer: 'body',
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                diff_mode: {
                    label: i18n._('Show Changes'),
                    type: 'toggleSwitch',
                    toggleSource: 'diff_mode',
                    dataTitle: i18n._('Show Changes'),
                    dataPlacement: 'right',
                    dataContainer: 'body',
                    awPopOver: "<p>" + i18n._("If enabled, show the changes made by Ansible tasks, where supported. This is equivalent to Ansible's --diff mode.") + "</p>",
                    subCheckbox: {
                        variable: 'ask_diff_mode_on_launch',
                        text: i18n._('Prompt on launch')
                    },
                },
                checkbox_group: {
                    label: i18n._('Options'),
                    type: 'checkbox_group',
                    class: 'Form-formGroup--fullWidth',
                    fields: [{
                        name: 'become_enabled',
                        label: i18n._('Enable Privilege Escalation'),
                        type: 'checkbox',
                        column: 2,
                        awPopOver: "<p>" + i18n.sprintf(i18n._("If enabled, run this playbook as an administrator. This is the equivalent of passing the %s option to the %s command."), '<code>--become</code>', '<code>ansible-playbook</code>') + " </p>",
                        dataPlacement: 'right',
                        dataTitle: i18n._('Become Privilege Escalation'),
                        dataContainer: "body",
                        labelClass: 'stack-inline',
                        ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                    }, {
                        name: 'allow_callbacks',
                        label: i18n._('Allow Provisioning Callbacks'),
                        type: 'checkbox',
                        ngChange: "toggleCallback('host_config_key')",
                        column: 2,
                        awPopOver: "<p>" + i18n._("Enables creation of a provisioning callback URL. Using the URL a host can contact {{BRAND_NAME}} and request a configuration update " +
                            "using this job template.") + "</p>",
                        dataPlacement: 'right',
                        dataTitle: i18n._('Allow Provisioning Callbacks'),
                        dataContainer: "body",
                        labelClass: 'stack-inline',
                        ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                    }, {
                        name: 'allow_simultaneous',
                        label: i18n._('Enable Concurrent Jobs'),
                        type: 'checkbox',
                        column: 2,
                        awPopOver: "<p>" + i18n._("If enabled, simultaneous runs of this job template will be allowed.") + "</p>",
                        dataPlacement: 'right',
                        dataTitle: i18n._('Enable Concurrent Jobs'),
                        dataContainer: "body",
                        labelClass: 'stack-inline',
                        ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                    }, {
                        name: 'use_fact_cache',
                        label: i18n._('Use Fact Cache'),
                        type: 'checkbox',
                        column: 2,
                        awPopOver: "<p>" + i18n._("If enabled, use cached facts if available and store discovered facts in the cache.") + "</p>",
                        dataPlacement: 'right',
                        dataTitle: i18n._('Use Fact Cache'),
                        dataContainer: "body",
                        labelClass: 'stack-inline',
                        ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
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
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
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
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)',
                    awRequiredWhen: {
                        reqExpression: 'allow_callbacks',
                        alwaysShowAsterisk: true
                    }
                },
                variables: {
                    label: i18n._('Extra Variables'),
                    type: 'textarea',
                    class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                    rows: 6,
                    "default": "---",
                    column: 2,
                    awPopOver: "<p>" + i18n.sprintf(i18n._("Pass extra command line variables to the playbook. This is the %s or %s command line parameter " +
                        "for %s. Provide key/value pairs using either YAML or JSON."), '<code>-e</code>', '<code>--extra-vars</code>', '<code>ansible-playbook</code>') + "</p>" +
                        "JSON:<br />\n" +
                        "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                        "YAML:<br />\n" +
                        "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n",
                    dataTitle: i18n._('Extra Variables'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subCheckbox: {
                        variable: 'ask_variables_on_launch',
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)' // TODO: get working
                }
            },

            buttons: { //for now always generates <button> tags
                cancel: {
                    ngClick: 'formCancel()',
                    ngShow: '(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                close: {
                    ngClick: 'formCancel()',
                    ngShow: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                save: {
                    ngClick: 'formSave()',    //$scope.function to call on click, optional
                    ngDisabled: "job_template_form.$invalid || credentialNotPresent",//true          //Disable when $pristine or $invalid, optional and when can_edit = false, for permission reasons
                    ngShow: '(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                }
            },

            related: {
                permissions: {
                    name: 'permissions',
                    awToolTip: i18n._('Please save before assigning permissions.'),
                    dataPlacement: 'top',
                    basePath: 'api/v2/job_templates/{{$stateParams.job_template_id}}/access_list/',
                    search: {
                        order_by: 'username'
                    },
                    type: 'collection',
                    title: i18n._('Permissions'),
                    iterator: 'permission',
                    index: false,
                    open: false,
                    ngClick: "$state.go('templates.editJobTemplate.permissions')",
                    actions: {
                        add: {
                            ngClick: "$state.go('.add')",
                            label: 'Add',
                            awToolTip: i18n._('Add a permission'),
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; ' + i18n._('ADD'),
                            ngShow: '(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
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
                            nosort: true,
                            class: 'col-lg-4 col-md-4 col-sm-4 col-xs-4',
                        },
                        team_roles: {
                            label: 'Team Roles',
                            type: 'team_roles',
                            nosort: true,
                            class: 'col-lg-5 col-md-5 col-sm-5 col-xs-4',
                        }
                    }
                },
                "notifications": {
                    include: "NotificationsList"
                },
                "completed_jobs": {
                    include: "CompletedJobsList"
                }
            },

            relatedButtons: {
                view_survey: {
                    ngClick: 'editSurvey()',
                    awFeature: 'surveys',
                    ngShow: '($state.is(\'templates.addJobTemplate\') || $state.is(\'templates.editJobTemplate\')) &&  survey_exists && !(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)',
                    label: i18n._('View Survey'),
                    class: 'Form-primaryButton'
                },
                add_survey: {
                    ngClick: 'addSurvey()',
                    ngShow: '($state.is(\'templates.addJobTemplate\') || $state.is(\'templates.editJobTemplate\')) && !survey_exists && (job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)',
                    awFeature: 'surveys',
                    awToolTip: '{{surveyTooltip}}',
                    dataPlacement: 'top',
                    label: i18n._('Add Survey'),
                    class: 'Form-primaryButton'
                },
                edit_survey: {
                    ngClick: 'editSurvey()',
                    awFeature: 'surveys',
                    ngShow: '($state.is(\'templates.addJobTemplate\') || $state.is(\'templates.editJobTemplate\')) && survey_exists && (job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)',
                    label: i18n._('Edit Survey'),
                    class: 'Form-primaryButton',
                    awToolTip: '{{surveyTooltip}}',
                    dataPlacement: 'top'
                }
            }
        };
        var itm;

        for (itm in JobTemplateFormObject.related) {
            if (JobTemplateFormObject.related[itm].include === "NotificationsList") {
                JobTemplateFormObject.related[itm] = _.clone(NotificationsList);
                JobTemplateFormObject.related[itm].ngClick = "$state.go('templates.editJobTemplate.notifications')";
                JobTemplateFormObject.related[itm].generateList = true;   // tell form generator to call list generator and inject a list
            }
            if (JobTemplateFormObject.related[itm].include === "CompletedJobsList") {
                JobTemplateFormObject.related[itm] = CompletedJobsList;
                JobTemplateFormObject.related[itm].ngClick = "$state.go('templates.editJobTemplate.completed_jobs')";
                JobTemplateFormObject.related[itm].generateList = true;
            }
        }

        return JobTemplateFormObject;
    };
}];
