/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  JobTemplates.js
 *  Form definition for Credential model
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
                options: [{ value: 'run', label: 'Run' }, { value: 'check', label: 'Check' }],
                default: 'run',
                addRequired: false, 
                editRequired: false
                },
            inventory: {
                label: 'Inventory',
                type: 'lookup',
                sourceModel: 'inventory',
                sourceField: 'name',
                addRequired: false,
                editRequired: false,
                ngClick: 'lookUpInventory()'
                },
            project: {
                label: 'Project',
                type: 'lookup',
                sourceModel: 'project',
                sourceField: 'name',
                addRequired: false,
                editRequired: false,
                ngClick: 'lookUpProject()'
                },
            playbook: {
                label: 'Playbook',
                type:'text',
                addRequired: false, 
                editRequired: false
                },
            credential: {
                label: 'Credential',
                type: 'lookup',
                sourceModel: 'credential',
                sourceField: 'name',
                addRequired: true,
                editRequired: true,
                ngClick: 'lookUpCredential()',
                addRequired: false, 
                editRequired: false
                },
            forks: {
                label: 'Forks',
                type: 'integer', 
                default: 0,
                min: 0,
                max: 10,
                addRequired: false, 
                editRequired: false
                },
            limit: {
                label: 'Limit',
                type: 'integer', 
                default: 0,
                min: 0,
                max: 10,
                addRequired: false, 
                editRequired: false
                },
            verbosity: {
                label: 'Verbosity',
                type: 'integer', 
                default: 0,
                min: 0,
                max: 5,
                addRequired: false, 
                editRequired: false
                },
            extra_vars: {
                label: 'Extra Variables',
                type: 'textarea',
                rows: 10,
                addRequired: false, 
                editRequired: false
                }
            },

        buttons: { //for now always generates <button> tags 
            save: { 
                label: 'Save', 
                icon: 'icon-ok',
                class: 'btn btn-success',
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: true          //Disable when $pristine or $invalid, optional
                },
            reset: { 
                ngClick: 'formReset()',
                label: 'Reset',
                icon: 'icon-remove',
                class: 'btn',
                ngDisabled: true          //Disabled when $pristine
                }
            },

        related: { //related colletions (and maybe items?)

            }
            
    }); //InventoryForm

