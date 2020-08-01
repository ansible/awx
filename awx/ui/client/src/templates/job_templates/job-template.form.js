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


export default ['NotificationsList', 'i18n',
function(NotificationsList, i18n) {
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
                    awPopOver: i18n._('For job templates, select run to execute the playbook. Select check to only check playbook syntax, test environment setup, and report problems without executing the playbook.'),
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
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate) || !canGetAllRelatedResources'
                },
                project: {
                    label: i18n._('Project'),
                    type: 'lookup',
                    list: 'ProjectList',
                    basePath: 'projects',
                    sourceModel: 'project',
                    sourceField: 'name',
                    required: true,
                    column: 1,
                    awPopOver: "<p>" + i18n._("Select the project containing the playbook you want this job to execute.") + "</p>",
                    dataTitle: i18n._('Project'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate) || !canGetAllRelatedResources',
                    awLookupWhen: 'canGetAllRelatedResources'
                },
                scm_branch: {
                    label: i18n._('SCM Branch'),
                    type: 'text',
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)',
                    ngShow: 'allow_branch_override',
                    column: 1,
                    awPopOver: "<p>" + i18n._("Branch to use in job run. Project default used if blank.") + "</p>",
                    dataTitle: i18n._('Project'),
                    subCheckbox: {
                        variable: 'ask_scm_branch_on_launch',
                        text: i18n._('Prompt on launch'),
                        ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                    },
                    dataPlacement: 'right',
                    dataContainer: "body"
                },
                playbook: {
                    label: i18n._('Playbook'),
                    type:'select',
                    defaultText: i18n._('Choose a playbook'),
                    ngOptions: 'book for book in playbook_options track by book',
                    ngShow: 'allow_playbook_selection',
                    ngDisabled: "!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate) || !canGetAllRelatedResources",
                    id: 'playbook-select',
                    required: true,
                    column: 1,
                    awPopOver: "<p>" + i18n._("Select the playbook to be executed by this job." +
                        "You can select from the dropdown or enter a file within the input.") + "</p>",
                    dataTitle: i18n._('Playbook'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    includePlaybookNotFoundError: true
                },
                credential: {
                    label: i18n._('Credentials'),
                    type: 'custom',
                    control: `
                        <multi-credential
                            credentials="credentials"
                            prompt="ask_credential_on_launch"
                            credential-not-present="credentialNotPresent"
                            selected-credentials="multiCredential.selectedCredentials"
                            credential-types="multiCredential.credentialTypes"
                            field-is-disabled="!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)">
                        </multi-credential>`,
                    awPopOver: i18n._('Select credentials that allow Tower to access the nodes this job will be ran against. You can only select one credential of each type. For machine credentials (SSH), checking  "Prompt on launch" without selecting credentials will require you to select a machine credential at run time. If you select credentials and check "Prompt on launch", the selected credential(s) become the defaults that can be updated at run time.'),
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
                    type: 'number',
                    integer: true,
                    min: 0,
                    default: 0,
                    spinner: true,
                    dataTitle: i18n._('Forks'),
                    dataPlacement: 'right',
                    dataContainer: 'body',
                    awPopOver: "<p>" + i18n._("The number of parallel or simultaneous processes to use while executing the playbook. An empty value, or a value less than 1 will use the Ansible default which is usually 5. The default number of forks can be overwritten with a change to ") + "<code class='popover-body_code-snippet'>ansible.cfg</code>. " + i18n._("Refer to the Ansible documentation for details about the configuration file.") + "</p>",
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                limit: {
                    label: i18n._('Limit'),
                    type: 'text',
                    column: 1,
                    awPopOver: i18n._('Provide a host pattern to further constrain the list of hosts that will be managed or affected by the playbook. Multiple patterns are allowed. Refer to Ansible documentation for more information and examples on patterns.'),
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
                job_tags: {
                    label: i18n._('Job Tags'),
                    type: 'select',
                    multiSelect: true,
                    'elementClass': 'Form-textInput',
                    ngOptions: 'tag.label for tag in job_tag_options track by tag.value',
                    column: 2,
                    awPopOver: i18n._('Tags are useful when you have a large playbook, and you want to run a specific part of a play or task. Use commas to separate multiple tags. Refer to Ansible Tower documentation for details on the usage of tags.'),
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
                    awPopOver: i18n._('Skip tags are useful when you have a large playbook, and you want to skip specific parts of a play or task. Use commas to separate multiple tags. Refer to Ansible Tower documentation for details on the usage of tags.'),
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
                    onError: {
                        ngShow: 'job_template_labels_isValid !== true',
                        text: i18n._('Max 512 characters per label.'),
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                custom_virtualenv: {
                    label: i18n._('Ansible Environment'),
                    type: 'select',
                    defaultText: i18n._('Use Default Environment'),
                    ngOptions: 'venv for venv in custom_virtualenvs_options track by venv',

                    awPopOver: "<p>" + i18n._("Select the custom Python virtual environment for this job template to run on.") + "</p>",
                    dataTitle: i18n._('Ansible Environment'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)',
                    ngShow: 'custom_virtualenvs_options.length > 1'
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
                job_slice_count: {
                    label: i18n._('Job Slicing'),
                    type: 'number',
                    integer: true,
                    min: 1,
                    default: 1,
                    spinner: true,
                    dataTitle: i18n._('Slice Job Count'),
                    dataPlacement: 'right',
                    dataContainer: 'body',
                    awPopOver: "<p>" + i18n._("Divide the work done by this job template into the specified number of job slices, each running the same tasks against a portion of the inventory.") + "</p>",
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                timeout: {
                    label: i18n._('Timeout'),
                    type: 'number',
                    integer: true,
                    min: 0,
                    default: 0,
                    spinner: true,
                    dataTitle: i18n._('Timeout'),
                    dataPlacement: 'right',
                    dataContainer: 'body',
                    awPopOver: "<p>" + i18n._("The amount of time (in seconds) to run before the task is canceled. Defaults to 0 for no job timeout.") + "</p>",
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                diff_mode: {
                    label: i18n._('Show Changes'),
                    type: 'toggleSwitch',
                    toggleSource: 'diff_mode',
                    dataTitle: i18n._('Show Changes'),
                    dataPlacement: 'right',
                    dataContainer: 'body',
                    awPopOver: "<p>" + i18n._("If enabled, show the changes made by Ansible tasks, where supported. This is equivalent to Ansible&#x2019s --diff mode.") + "</p>",
                    subCheckbox: {
                        variable: 'ask_diff_mode_on_launch',
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                },
                checkbox_group: {
                    label: i18n._('Options'),
                    type: 'checkbox_group',
                    fields: [{
                        name: 'become_enabled',
                        label: i18n._('Enable Privilege Escalation'),
                        type: 'checkbox',
                        column: 2,
                        awPopOver: i18n._('If enabled, run this playbook as an administrator.'),
                        dataPlacement: 'right',
                        dataTitle: i18n._('Enable Privilege Escalation'),
                        dataContainer: "body",
                        ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                    }, {
                        name: 'allow_callbacks',
                        label: i18n._('Enable Provisioning Callbacks'),
                        type: 'checkbox',
                        ngChange: "toggleCallback('host_config_key')",
                        column: 2,
                        awPopOver: "<p>" + i18n._("Enables creation of a provisioning callback URL. Using the URL a host can contact {{BRAND_NAME}} and request a configuration update " +
                            "using this job template.") + "</p>",
                        dataPlacement: 'right',
                        dataTitle: i18n._('Enable Provisioning Callbacks'),
                        dataContainer: "body",
                        ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                    }, {
                        name: 'enable_webhook',
                        label: i18n._('Enable Webhook'),
                        type: 'checkbox',
                        column: 2,
                        awPopOver: "<p>" + i18n._("Enable webhook for this job template.") + "</p>",
                        dataPlacement: 'right',
                        dataTitle: i18n._('Enable Webhook'),
                        dataContainer: "body",
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
                        ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                    }, {
                        name: 'use_fact_cache',
                        label: i18n._('Enable Fact Cache'),
                        type: 'checkbox',
                        column: 2,
                        awPopOver: "<p>" + i18n._("If enabled, use cached facts if available and store discovered facts in the cache.") + "</p>",
                        dataPlacement: 'right',
                        dataTitle: i18n._('Enable Fact Cache'),
                        dataContainer: "body",
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
                    genHash: true,
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
                webhook_service: {
                    label: i18n._('Webhook Service'),
                    type:'select',
                    defaultText: i18n._('Choose a Webhook Service'),
                    ngOptions: 'svc.label for svc in webhook_service_options track by svc.value',
                    ngShow: "enable_webhook  && enable_webhook !== 'false'",
                    ngDisabled: "!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate) || !canGetAllRelatedResources",
                    id: 'webhook-service-select',
                    column: 1,
                    awPopOver: "<p>" + i18n._("Select a webhook service.") + "</p>",
                    dataTitle: i18n._('Webhook Service'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                },
                webhook_url: {
                    label: i18n._('Webhook URL'),
                    type: 'text',
                    ngShow: "job_template_obj && enable_webhook && enable_webhook !== 'false'",
                    awPopOver: "webhook_url_help",
                    awPopOverWatch: "webhook_url_help",
                    dataPlacement: 'top',
                    dataTitle: i18n._('Webhook URL'),
                    dataContainer: "body",
                    readonly: true
                },
                webhook_key: {
                    label: i18n._('Webhook Key'),
                    type: 'text',
                    ngShow: "enable_webhook && enable_webhook !== 'false'",
                    genHash: true,
                    genHashButtonTemplate: `
                        <span
                            ng-if="job_template_obj && webhook_service.value && currentlySavedWebhookKey === webhook_key"
                            class="input-group-btn input-group-prepend"
                        >
                            <button
                                aria-label="${i18n._('Rotate Webhook Key')}"
                                type="button"
                                class="btn Form-lookupButton"
                                ng-click="handleWebhookKeyButtonClick()"
                                aw-tool-tip="${i18n._('Rotate Webhook Key')}"
                                data-placement="top"
                                id="job_template_webhook_key_gen_btn"
                            >
                                <i class="fa fa-refresh"></i>
                            </button>
                        </span>
                    `,
                    genHashButtonClickHandlerName: "handleWebhookKeyButtonClick",
                    awPopOver: "webhook_key_help",
                    awPopOverWatch: "webhook_key_help",
                    dataPlacement: 'right',
                    dataTitle: i18n._("Webhook Key"),
                    dataContainer: "body",
                    readonly: true,
                    required: false,
                },
                webhook_credential: {
                    label: i18n._('Webhook Credential'),
                    type: 'custom',
                    ngShow: "enable_webhook  && enable_webhook !== 'false'",
                    control: `
                        <webhook-credential-input
                            is-field-disabled="!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate) || !(webhookCredential.modalBaseParams.credential_type__namespace)"
                            tag-name="webhookCredential.name"
                            on-lookup-click="handleWebhookCredentialLookupClick"
                            on-tag-delete="handleWebhookCredentialTagDelete"
                        </webhook-credential-input>`,
                    awPopOver: "<p>" + i18n._("Optionally, select the credential to use to send status updates back to the webhook service") + "</p>",
                    dataTitle: i18n._('Webhook Credential'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngDisabled: '!(webhook_service || webhook_service.value)',
                    required: false,
                },
                extra_vars: {
                    label: i18n._('Extra Variables'),
                    type: 'textarea',
                    class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                    rows: 6,
                    "default": "---",
                    column: 2,
                    awPopOver: i18n._('Pass extra command line variables to the playbook. Provide key/value pairs using either YAML or JSON. Refer to the Ansible Tower documentation for example syntax.'),
                    dataTitle: i18n._('Extra Variables'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    id: 'extra_vars',
                    subCheckbox: {
                        variable: 'ask_variables_on_launch',
                        text: i18n._('Prompt on launch')
                    },
                    ngDisabled: '!(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)' // TODO: get working
                }
            },

            buttons: { //for now always generates <button> tags
                launch: {
                    component: 'at-launch-template',
                    templateObj: 'job_template_obj',
                    ngShow: '(job_template_obj.summary_fields.user_capabilities.start || canAddJobTemplate)',
                    ngDisabled: 'disableLaunch || job_template_form.$dirty',
                    showTextButton: 'true'
                },
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
                    ngDisabled: "job_template_form.$invalid",//true          //Disable when $pristine or $invalid, optional and when can_edit = false, for permission reasons
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
                            actionClass: 'at-Button--add',
                            actionId: 'button-add--permission',
                            ngShow: '(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)'
                        }
                    },

                    fields: {
                        username: {
                            key: true,
                            label: 'User',
                            linkBase: 'users',
                            columnClass: 'col-sm-3 col-xs-4'
                        },
                        role: {
                            label: 'Role',
                            type: 'role',
                            nosort: true,
                            columnClass: 'col-sm-4 col-xs-4',
                        },
                        team_roles: {
                            label: 'Team Roles',
                            type: 'team_roles',
                            nosort: true,
                            columnClass: 'col-sm-5 col-xs-4',
                        }
                    }
                },
                "notifications": {
                    include: "NotificationsList"
                },
                "completed_jobs": {
                    title: i18n._('Completed Jobs'),
                    skipGenerator: true,
                    ngClick: "$state.go('templates.editJobTemplate.completed_jobs')"
                },
                "schedules": {
                    title: i18n._('Schedules'),
                    skipGenerator: true,
                    ngClick: "$state.go('templates.editJobTemplate.schedules')"
                }
            },

            relatedButtons: {
                view_survey: {
                    ngClick: 'editSurvey()',
                    ngShow: '($state.is(\'templates.addJobTemplate\') || $state.is(\'templates.editJobTemplate\')) &&  survey_exists && !(job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)',
                    label: i18n._('View Survey'),
                    class: 'Form-primaryButton'
                },
                add_survey: {
                    ngClick: 'addSurvey()',
                    ngShow: '($state.is(\'templates.addJobTemplate\') || $state.is(\'templates.editJobTemplate\')) && !survey_exists && (job_template_obj.summary_fields.user_capabilities.edit || canAddJobTemplate)',
                    awToolTip: '{{surveyTooltip}}',
                    dataPlacement: 'top',
                    label: i18n._('Add Survey'),
                    class: 'Form-primaryButton'
                },
                edit_survey: {
                    ngClick: 'editSurvey()',
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
        }

        return JobTemplateFormObject;
    };
}];
