/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Projects.js
 *
 *  Form definition for Projects model
 *
 *  
 */
angular.module('ProjectFormDefinition', [])
    .value(
    'ProjectsForm', {
        
        addTitle: 'Create Project',                             //Title in add mode
        editTitle: '{{ name }}',                                //Title in edit mode
        name: 'project',                                        //entity or model name in singular form
        well: true,                                             //Wrap the form with TB well/           

        fields: {
            name: {
                label: 'Name',
                type: 'text',
                addRequired: true,
                editRequired: true,
                capitalize: true
                },
            description: { 
                label: 'Description',
                type: 'text',
                addRequired: false,
                editRequired: false
                },
            base_dir: {
                label: 'Project Base Path',
                type: 'textarea',
                "class": 'span6',
                showonly: true,
                awPopOver: '<p>Base path used for locating playbooks. Directories found inside this path will be listed in the Project Path drop-down. ' +
                  'Together the base path and selected project path provide the full path used to locate playbooks for this project.</p>' + 
                  '<p>Use PROJECTS_ROOT in your environment settings file to determine the base path value.</p>',
                dataTitle: 'Project Base Path',
                dataPlacement: 'right'
                },
            local_path: { 
                label: 'Project Path',
                type: 'select',
                id: 'local-path-select',
                ngOptions: 'path for path in project_local_paths',
                addRequired: true,
                editRequired: true,
                awPopOver: '<p>Select from the list of directories found in the base path.' +
                  'Together the base path and selected project path provide the full path used to locate playbooks for this project.</p>' + 
                  '<p>Use PROJECTS_ROOT in your environment settings file to determine the base path value.</p>',
                dataTitle: 'Project Path',
                dataPlacement: 'right'
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

            }

    }); // Form

    