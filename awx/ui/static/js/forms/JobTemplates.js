/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobTemplates.js
 *  Form definition for Job Template model
 *
 *  To get the JobTemplateForm object: JobTemplateForm();
 *
 */
/**
 * @ngdoc function
 * @name forms.function:JobTemplate
 * @description This form is for adding/editing a Job Template
*/
'use strict';

angular.module('JobTemplateFormDefinition', ['SchedulesListDefinition', 'CompletedJobsDefinition'])

    .value ('JobTemplateFormObject', {

        addTitle: 'Create Job Templates',
        editTitle: '{{ name }}',
        name: 'job_templates',
        twoColumns: true,
        well: true,
        base: 'job_templates',
        collapse: true,
        collapseTitle: "Properties",
        collapseMode: 'edit',
        collapseOpenFirst: true,   //Always open first panel

        actions: {
            submit: {
                ngClick: 'launch()',
                awToolTip: 'Start a job using this template',
                dataPlacement: 'top',
                mode: 'edit'
            },
            stream: {
                'class': "btn-primary btn-xs activity-btn",
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                dataPlacement: "top",
                icon: "icon-comments-alt",
                mode: 'edit',
                iconSize: 'large'
            }
        },

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
                addRequired: false,
                editRequired: false,
                column: 1
            },
            job_type: {
                label: 'Job Type',
                type: 'select',
                ngOptions: 'type.label for type in job_type_options',
                "default": 0,
                addRequired: true,
                editRequired: true,
                column: 1,
                awPopOver: "<p>When this template is submitted as a job, setting the type to <em>run</em> will execute the playbook, running tasks " +
                    " on the selected hosts.</p> <p>Setting the type to <em>check</em> will not execute the playbook. Instead, ansible will check playbook " +
                    " syntax, test environment setup and report problems.</p>",
                dataTitle: 'Job Type',
                dataPlacement: 'right',
                dataContainer: "body"
            },
            inventory: {
                label: 'Inventory',
                type: 'lookup',
                sourceModel: 'inventory',
                sourceField: 'name',
                ngClick: 'lookUpInventory()',
                awRequiredWhen: {variable: "inventoryrequired", init: "true" },
                column: 1,
                awPopOver: "<p>Select the inventory containing the hosts you want this job to manage.</p>",
                dataTitle: 'Inventory',
                dataPlacement: 'right',
                dataContainer: "body"
            },
            project: {
                label: 'Project',
                type: 'lookup',
                sourceModel: 'project',
                sourceField: 'name',
                ngClick: 'lookUpProject()',
                awRequiredWhen: {variable: "projectrequired", init: "true" },
                column: 1,
                awPopOver: "<p>Select the project containing the playbook you want this job to execute.</p>",
                dataTitle: 'Project',
                dataPlacement: 'right',
                dataContainer: "body"
            },
            playbook: {
                label: 'Playbook',
                type:'select',
                ngOptions: 'book for book in playbook_options',
                id: 'playbook-select',
                awRequiredWhen: {variable: "playbookrequired", init: "true" },
                column: 1,
                awPopOver: "<p>Select the playbook to be executed by this job.</p>",
                dataTitle: 'Playbook',
                dataPlacement: 'right',
                dataContainer: "body"
            },
            credential: {
                label: 'Machine Credential',
                type: 'lookup',
                sourceModel: 'credential',
                sourceField: 'name',
                ngClick: 'lookUpCredential()',
                addRequired: false,
                editRequired: false,
                column: 1,
                awPopOver: "<p>Select the credential you want the job to use when accessing the remote hosts. Choose the credential containing " +
                 " the username and SSH key or password that Ansbile will need to log into the remote hosts.</p>",
                dataTitle: 'Credential',
                dataPlacement: 'right',
                dataContainer: "body"
            },
            cloud_credential: {
                label: 'Cloud Credential',
                type: 'lookup',
                sourceModel: 'cloud_credential',
                sourceField: 'name',
                ngClick: 'lookUpCloudcredential()',
                addRequired: false,
                editRequired: false,
                column: 1,
                awPopOver: "<p>Selecting an optional cloud credential in the job template will pass along the access credentials to the " +
                    "running playbook, allowing provisioning into the cloud without manually passing parameters to the included modules.</p>",
                dataTitle: 'Cloud Credential',
                dataPlacement: 'right',
                dataContainer: "body"
            },
            forks: {
                label: 'Forks',
                id: 'forks-number',
                type: 'number',
                integer: true,
                min: 0,
                spinner: true,
                "default": '0',
                addRequired: false,
                editRequired: false,
                'class': "input-small",
                column: 1,
                awPopOver: '<p>The number of parallel or simultaneous processes to use while executing the playbook. 0 signifies ' +
                    'the default value from the <a href=\"http://docs.ansible.com/intro_configuration.html#the-ansible-configuration-file\" ' +
                    ' target=\"_blank\">ansible configuration file</a>.</p>',
                dataTitle: 'Forks',
                dataPlacement: 'right',
                dataContainer: "body"
            },
            limit: {
                label: 'Limit',
                type: 'text',
                addRequired: false,
                editRequired: false,
                column: 1,
                awPopOver: "<p>Provide a host pattern to further constrain the list of hosts that will be managed or affected by the playbook. " +
                    "Multiple patterns can be separated by &#59; &#58; or &#44;</p><p>For more information and examples see " +
                    "<a href=\"http://docs.ansible.com/intro_patterns.html\" target=\"_blank\">the Patterns topic at docs.ansible.com</a>.</p>",
                dataTitle: 'Limit',
                dataPlacement: 'right',
                dataContainer: "body"
            },
            verbosity: {
                label: 'Verbosity',
                type: 'select',
                ngOptions: 'v.label for v in verbosity_options',
                "default": 0,
                addRequired: true,
                editRequired: true,
                column: 1,
                awPopOver: "<p>Control the level of output ansible will produce as the playbook executes.</p>",
                dataTitle: 'Verbosity',
                dataPlacement: 'right',
                dataContainer: "body"
            },
            job_tags: {
                label: 'Job Tags',
                type: 'textarea',
                rows: 1,
                addRequired: false,
                editRequired: false,
                'class': 'span12',
                column: 2,
                awPopOver: "<p>Provide a comma separated list of tags.</p>\n" +
                    "<p>Tags are useful when you have a large playbook, and you want to run a specific part of a play or task.</p>" +
                    "<p>For example, you might have a task consisiting of a long list of actions. Tag values can be assigned to each action. " +
                    "Suppose the actions have been assigned tag values of &quot;configuration&quot;, &quot;packages&quot; and &quot;install&quot;.</p>" +
                    "<p>If you just want to run the &quot;configuration&quot; and &quot;packages&quot; actions, you would enter the following here " +
                    "in the Job Tags field:</p>\n<blockquote>configuration,packages</blockquote>\n",
                dataTitle: "Job Tags",
                dataPlacement: "right",
                dataContainer: "body"
            },
            variables: {
                label: 'Extra Variables',
                type: 'textarea',
                rows: 6,
                "class": 'span12',
                addRequired: false,
                editRequired: false,
                "default": "---",
                column: 2,
                awPopOver: "<p>Pass extra command line variables to the playbook. This is the -e or --extra-vars command line parameter " +
                    "for ansible-playbook. Provide key/value pairs using either YAML or JSON.</p>" +
                    "JSON:<br />\n" +
                    "<blockquote>{<br />\"somevar\": \"somevalue\",<br />\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n",
                dataTitle: 'Extra Variables',
                dataPlacement: 'right',
                dataContainer: "body"
            },
            ask_variables_on_launch: {
                label: 'Prompt for Extra Variables',
                type: 'checkbox',
                addRequired: false,
                editRequird: false,
                trueValue: 'true',
                falseValue: 'false',
                column: 2,
                awPopOver: "<p>If checked, user will be prompted at job launch with a dialog allowing override of the extra variables setting.</p>",
                dataPlacement: 'right',
                dataTitle: 'Prompt for Extra Variables',
                dataContainer: "body"
            },
            allow_callbacks: {
                label: 'Allow Provisioning Callbacks',
                type: 'checkbox',
                addRequired: false,
                editRequird: false,
                trueValue: 'true',
                falseValue: 'false',
                ngChange: "toggleCallback('host_config_key')",
                column: 2,
                awPopOver: "<p>Enables creation of a provisioning callback URL. Using the URL a host can contact Tower and request a configuration update " +
                    "using this job template.</p>",
                dataPlacement: 'right',
                dataTitle: 'Allow Provisioning Callbacks',
                dataContainer: "body"
            },
            callback_url: {
                label: 'Provisioning Callback URL',
                type: 'text',
                addRequired: false,
                editRequired: false,
                readonly: true,
                ngShow: "allow_callbacks",
                column: 2,
                awPopOver: "callback_help",
                awPopOverWatch: "callback_help",
                dataPlacement: 'right',
                dataTitle: 'Provisioning Callback URL',
                dataContainer: "body"
            },
            host_config_key: {
                label: 'Host Config Key',
                type: 'text',
                ngShow: "allow_callbacks",
                ngChange: "configKeyChange()",
                genMD5: true,
                column: 2,
                awPopOver: "callback_help",
                awPopOverWatch: "callback_help",
                dataPlacement: 'right',
                dataTitle: "Host Config Key",
                dataContainer: "body"
            }
        },

        buttons: { //for now always generates <button> tags
            save: {
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: true          //Disable when $pristine or $invalid, optional
            },
            reset: {
                ngClick: 'formReset()',
                ngDisabled: true          //Disabled when $pristine
            }
        },

        related: {

            schedules: {
                include: "SchedulesList"
            },
            "completed_jobs": {
                include: "CompletedJobsList"
            }
        },

        relatedSets: function(urls) {
            return {
                completed_jobs: {
                    iterator: 'completed_job',
                    url: urls.jobs + '?or__status=successful&or__status=failed&or__status=error&or__status=canceled'
                },
                schedules: {
                    iterator: 'schedule',
                    url: urls.schedules
                }
            };
        }
    })

    .factory('JobTemplateForm', ['JobTemplateFormObject', 'SchedulesList', 'CompletedJobsList',
    function(JobTemplateFormObject, SchedulesList, CompletedJobsList) {
        return function() {
            var itm;

            for (itm in JobTemplateFormObject.related) {
                if (JobTemplateFormObject.related[itm].include === "SchedulesList") {
                    JobTemplateFormObject.related[itm] = SchedulesList;
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
