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
        well: true,

        fields: {
            name: {
                label: 'Name',
                type: 'text',
                addRequired: true,
                editRequired: true
                },
            description: { 
                label: 'Description',
                type: 'text',
                addRequired: false,
                editRequired: false
                },
            job_type: {
                label: 'Job Type',
                type: 'select',
                ngOptions: 'type.label for type in job_type_options',
                default: 'run',
                addRequired: true, 
                editRequired: true
                },
            inventory: {
                label: 'Inventory',
                type: 'lookup',
                sourceModel: 'inventory',
                sourceField: 'name',
                addRequired: true,
                editRequired: true,
                ngClick: 'lookUpInventory()'
                },
            project: {
                label: 'Project',
                type: 'lookup',
                sourceModel: 'project',
                sourceField: 'name',
                addRequired: true,
                editRequired: true,
                ngClick: 'lookUpProject()',
                },
            playbook: {
                label: 'Playbook',
                type:'select',
                ngOptions: 'book for book in playbook_options',
                id: 'playbook-select',
                addRequired: true, 
                editRequired: true
                },
            credential: {
                label: 'Credential',
                type: 'lookup',
                sourceModel: 'credential',
                sourceField: 'name',
                ngClick: 'lookUpCredential()',
                addRequired: false, 
                editRequired: false
                },
            forks: {
                label: 'Forks',
                type: 'number', 
                integer: true,
                min: 0,
                max: 100,
                default: 0,
                addRequired: false, 
                editRequired: false
                },
            limit: {
                label: 'Limit',
                type: 'text', 
                addRequired: false, 
                editRequired: false
                },
            verbosity: {
                label: 'Verbosity',
                type: 'number',
                integer: true,
                default: 0,
                min: 0,
                max: 3,
                addRequired: false, 
                editRequired: false
                },
            extra_vars: {
                label: 'Extra Variables',
                type: 'textarea',
                rows: 6,
                class: 'span4',
                addRequired: false, 
                editRequired: false
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

        related: { //related colletions (and maybe items?)
            
            jobs:  {
                type: 'collection',
                title: 'Jobs',
                iterator: 'job',
                open: false,
                
                actions: { 
                    },
                
                fields: {
                    name: {
                        key: true,
                        label: 'Name'
                        },
                    description: {
                        label: 'Description'
                        }
                    },
                
                fieldActions: {
                    edit: {
                        ngClick: "edit('jobs', \{\{ job.id \}\}, '\{\{ job.name \}\}')",
                        icon: 'icon-edit'
                        }
                    }
                },
            }
            
    }); //InventoryForm

