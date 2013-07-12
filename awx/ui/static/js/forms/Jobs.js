/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Jobs.js
 *  Form definition for Jobs model
 *
 *  @dict
 */
angular.module('JobFormDefinition', [])
    .value(
    'JobForm', {
        
        addTitle: 'Create Job',                          //Legend in add mode
        editTitle: '{{ name }}',                         //Legend in edit mode
        name: 'jobs',
        well: true,
        twoColumns: true,
        
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
                "default": 'run',
                addRequired: true, 
                editRequired: true,
                awPopOver: "<p>When this template is submitted as a job, setting the type to <em>run</em> will execute the playbook, running tasks " +
                    " on the selected hosts.</p> <p>Setting the type to <em>check</em> will not execute the playbook. Instead, ansible will check playbook " +
                    " syntax, test environment setup and report problems.</p>",
                dataTitle: 'Job Type',
                dataPlacement: 'right',
                column: 1
                },
            inventory: {
                label: 'Inventory',
                type: 'lookup',
                sourceModel: 'inventory',
                sourceField: 'name',
                addRequired: true,
                editRequired: true,
                ngClick: 'lookUpInventory()',
                column: 1
                },
            project: {
                label: 'Project',
                type: 'lookup',
                sourceModel: 'project',
                sourceField: 'name',
                addRequired: true,
                editRequired: true,
                ngClick: 'lookUpProject()',
                column: 1
                },
            playbook: {
                label: 'Playbook',
                type:'select',
                ngOptions: 'book for book in playbook_options',
                id: 'playbook-select',
                addRequired: true, 
                editRequired: true,
                column: 1
                },
            credential: {
                label: 'Credential',
                type: 'lookup',
                sourceModel: 'credential',
                sourceField: 'name',
                ngClick: 'lookUpCredential()',
                addRequired: false, 
                editRequired: false,
                column: 2
                },
            forks: {
                label: 'Forks',
                id: 'forks-number',
                type: 'number', 
                integer: true,
                min: 0,
                max: 100,
                slider: true, 
                "class": 'input-mini',
                "default": '0',
                addRequired: false, 
                editRequired: false,
                column: 2,
                awPopOver: "<p>The number of parallel or simultaneous processes to use while executing the playbook. Provide a value between 0 and 100. " +
                    "A value of zero will use the ansible default setting of 5 parallel processes.</p>",
                dataTitle: 'Forks',
                dataPlacement: 'left'
                },
            limit: {
                label: 'Limit',
                type: 'text', 
                addRequired: false, 
                editRequired: false,
                column: 2,
                awPopOver: "<p>Provide a host pattern to further constrain the list of hosts that will be managed or affected by the playbook. " +
                    "Multiple patterns can be separated by &#59; &#58; or &#44;</p><p>For more information and examples see the " +
                    "<a href=\"http://ansible.cc/docs/patterns.html#selecting-targets\" target=\"_blank\">Selecting Targets section</a> under Inventory and Patterns " + 
                    " in the Ansible documentation.</p>",
                dataTitle: 'Limit',
                dataPlacement: 'left'
                },
            verbosity: {
                label: 'Verbosity',
                type: 'select',
                ngOptions: 'v.label for v in verbosity_options',
                "default": 0,
                addRequired: true, 
                editRequired: true,
                column: 2,
                awPopOver: "<p>Control the level of output ansible will produce as the playbook executes.</p>",
                dataTitle: 'Verbosity',
                dataPlacement: 'left'
                },
            extra_vars: {
                label: 'Extra Variables',
                type: 'textarea',
                rows: 6,
                "class": 'span12',
                addRequired: false, 
                editRequired: false,
                awPopOver: "<p>Pass extra command line variables to the playbook. This is the -e or --extra-vars command line parameter " +
                    "for ansible-playbook. Provide key=value pairs or JSON. <p><a href=\"http://www.ansibleworks.com/docs/playbooks2.html" + 
                    "#passing-variables-on-the-command-line\" target=\"_blank\">Click here to view documentation and examples.</a></p>",
                column: 2
                },
            allow_callbacks: {
                label: 'Allow Callbacks',
                type: 'checkbox',
                addRequired: false, 
                editRequird: false,
                trueValue: 'true',
                falseValue: 'false',
                ngChange: "toggleCallback('host_config_key')",
                "class": "span12",
                column: 2,
                awPopOver: "<p>Create a callback URL a host can use to contact the AWX server and request a configuration update " + 
                    "using the job template.  The URL will look like the following:</p>\n" +
                    "<p class=\"code-breakable\">http://your.server.com:999/api/v1/job_templates/1/callback/</p>" +
                    "<p>The request from the host must be a POST. Here is an example using curl:</p>\n" +
                    "<p class=\"code-breakable\">curl --data \"host_config_key=5a8ec154832b780b9bdef1061764ae5a\" " + 
                    "http://your.server.com:999/api/v1/job_templates/1/callback/</p>\n" +
                    "<p>Note the requesting host must be defined in your inventory. If ansible fails to locate the host either by name or IP address " +
                    "in one of your defined inventories, the request will be denied.</p>" +
                    "<p>Successful requests will result in an entry on the Jobs tab, where the results and history can be viewed.</p>",
                detailPlacement: 'left',
                dataContainer: '#jobs',
                dataTitle: 'Callback URL'
                },
            callback_url: {d
                label: 'Callback URL', 
                type: 'text',
                addRequired: false, 
                editRequired: false,
                readonly: true,
                column: 2,
                required: false,
                'class': 'span12',
                awPopOver: "<p>Using this URL a host can contact the AWX server and request a configuration update using the job " +
                    "template. The request from the host must be a POST. Here is an example using curl:</p>\n" +
                    "<p class=\"code-breakable\">curl --data \"host_config_key=5a8ec154832b780b9bdef1061764ae5a\" " + 
                    "http://your.server.com:999/api/v1/job_templates/1/callback/</p>\n" +
                    "<p>Note the requesting host must be defined in your inventory. If ansible fails to locate the host either by name or IP address " +
                    "in one of your defined inventories, the request will be denied.</p>" +
                    "<p>Successful requests will result in an entry on the Jobs tab, where the results and history can be viewed.</p>",
                detailPlacement: 'left',
                dataContainer: '#jobs',
                dataTitle: 'Callback URL'
                },
            host_config_key: {
                label: 'Host Config Key',
                type: 'text',
                ngShow: "allow_callbacks",
                genMD5: true,
                column: 2,
                awPopOver: "<p>When contacting the AWX server using the callback URL, the calling host must authenticate by including " +
                    "this key in the POST data of the request. Here's an example using curl:</p>\n" +
                    "<p class=\"code-breakable\">curl --data \"host_config_key=5a8ec154832b780b9bdef1061764ae5a\" " + 
                    "http://your.server.com:999/api/v1/job_templates/1/callback/</p>\n",
                detailPlacement: 'left',
                dataContainer: '#jobs'
                }
            },

        buttons: { //for now always generates <button> tags 
            save: { 
                label: 'Save', 
                icon: 'icon-ok',
                "class": 'btn-success',
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: true          //Disable when $pristine or $invalid, optional
                },
            reset: { 
                ngClick: 'formReset()',
                label: 'Reset',
                icon: 'icon-remove',
                ngDisabled: true          //Disabled when $pristine
                }
            },

        statusFields: {
            status: {
                label: 'Job Status <span class="job-detail-status job-\{\{ status \}\}"><i class="icon-circle"></i> \{\{ status \}\}</span>',
                type: 'text',
                readonly: true,
                control: false
                },
            created: {
                label: 'Date',
                type: 'text',
                readonly: true
                },
            result_stdout: {
                label: 'Standard Out', 
                type: 'textarea',
                readonly: true,
                rows: 20,
                "class": 'span12'
                },
            result_traceback: {
                label: 'Traceback',
                type: 'textarea', 
                readonly: true,
                rows: 10,
                "class": 'span12',
                ngShow: "result_traceback != ''"
                }
            },

        statusActions: {
            refresh: {
                label: 'Refresh',
                icon: 'icon-refresh',
                ngClick: "refresh()",
                "class": 'btn-small btn-success',
                awToolTip: 'Refresh job status &amp; output',
                mode: 'all'
                },
            summary: {
                label: 'Hosts',
                icon: 'icon-th-large',
                ngClick: "jobSummary()",
                "class": 'btn btn-small',
                awToolTip: 'View host summary',
                mode: 'all'
                },
            events: {
                label: 'Events',
                icon: 'icon-list-ul',
                ngClick: "jobEvents()",
                "class": 'btn btn-small',
                awToolTip: 'Edit job events',
                mode: 'all'        
                }
            },

        related: { //related colletions (and maybe items?)
           
            }
            
    }); //Form

