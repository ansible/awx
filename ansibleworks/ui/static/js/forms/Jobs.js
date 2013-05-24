/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Jobs.js
 *  Form definition for Jobs model
 *
 *
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
                default: 'run',
                addRequired: true, 
                editRequired: true,
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
                type: 'number', 
                integer: true,
                min: 0,
                max: 100,
                default: 0,
                addRequired: false, 
                editRequired: false,
                column: 2
                },
            limit: {
                label: 'Limit',
                type: 'text', 
                addRequired: false, 
                editRequired: false,
                column: 2
                },
            verbosity: {
                label: 'Verbosity',
                type: 'number',
                integer: true,
                default: 0,
                min: 0,
                max: 3,
                addRequired: false, 
                editRequired: false,
                column: 2
                },
            extra_vars: {
                label: 'Extra Variables',
                type: 'textarea',
                rows: 6,
                class: 'span12',
                addRequired: false, 
                editRequired: false,
                column: 2
                }
            },

        buttons: { //for now always generates <button> tags 
            save: { 
                label: 'Save', 
                icon: 'icon-ok',
                class: 'btn-success',
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
            result_stdout: {
                label: 'Standard Out', 
                type: 'textarea',
                readonly: true,
                rows: 20,
                class: 'span12'
                },
            result_traceback: {
                label: 'Traceback',
                type: 'textarea', 
                readonly: true,
                rows: 10,
                class: 'span12'
                }
            },

        statusActions: {
            refresh: {
                label: 'Refresh',
                icon: 'icon-refresh',
                ngClick: "refresh()",
                class: 'btn-small btn-success',
                awToolTip: 'Refresh job status &amp; output',
                mode: 'all'
                },
            summary: {
                label: 'Hosts',
                icon: 'icon-filter',
                ngClick: "jobSummary()",
                class: 'btn-info btn-small',
                awToolTip: 'View host summary',
                mode: 'all'
                },
            events: {
                label: 'Events',
                icon: 'icon-list-ul',
                ngClick: "jobEvents()",
                class: 'btn-info btn-small',
                awToolTip: 'View job events',
                mode: 'all',             
                }
            },

        related: { //related colletions (and maybe items?)
           
            }
            
    }); //Form

