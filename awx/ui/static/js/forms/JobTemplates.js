/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  JobTemplates.js
 *  Form definition for Job Template model
 *
 *  
 */
angular.module('JobTemplateFormDefinition', [])
    .value(
    'JobTemplateForm', {
        
        addTitle: 'Create Job Templates',                          //Legend in add mode
        editTitle: '{{ name }}',                                   //Legend in edit mode
        name: 'job_templates',
        twoColumns: true,
        well: true,

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
                dataPlacement: 'right'
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
                column: 1
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
                dataPlacement: 'left'
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
                column: 2
                },
            host_config_key: {
                label: 'Host Config Key',
                type: 'text',
                ngShow: "allow_callbacks",
                genMD5: true,
                column: 2
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

        related: { //related colletions (and maybe items?)
            
            jobs:  {
                type: 'collection',
                title: 'Jobs',
                iterator: 'job',
                index: false,
                open: false,
                
                actions: { 
                    },
                
                fields: {
                    id: {
                        label: 'Job ID',
                        key: true,
                        desc: true,
                        searchType: 'int'   
                        },
                    name: {
                        label: 'Name',
                        link: true
                        },
                    description: {
                        label: 'Description'
                        },
                    status: {
                        label: 'Status',
                        icon: 'icon-circle',
                        "class": 'job-\{\{ job.status \}\}',
                        searchType: 'select',
                        searchOptions: [
                            { name: "new", value: "new" }, 
                            { name: "pending", value: "pending" },
                            { name: "running", value: "running" }, 
                            { name: "successful", value: "successful" },
                            { name: "error", value: "error" },
                            { name: "failed", value: "failed" },
                            { name: "canceled", value: "canceled" } ]
                        }
                    },
                
                fieldActions: {
                    edit: {
                        label: 'View',
                        ngClick: "edit('jobs', \{\{ job.id \}\}, '\{\{ job.name \}\}')",
                        icon: 'icon-zoom-in'
                        }
                    }
                }
            }
            
    }); //InventoryForm

