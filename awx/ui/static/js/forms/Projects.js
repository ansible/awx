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
        
        addTitle: 'Create Project',                             // Title in add mode
        editTitle: '{{ name }}',                                // Title in edit mode
        name: 'project',                                        // entity or model name in singular form
        well: true,                                             // Wrap the form with TB well

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
            organization: {
                label: 'Organization',
                type: 'lookup',
                sourceModel: 'organization',
                sourceField: 'name',
                addRequired: true,
                editRequired: false,
                excludeMode: 'edit',
                ngClick: 'lookUpOrganization()',
                awRequiredWhen: {variable: "organizationrequired", init: "true" },
                awPopOver: '<p>A project must have at least one organization. Pick one organization now to create the project, and then after ' +
                  'the project is created you can add additional organizations.' ,
                dataTitle: 'Organization',
                dataContainer: 'body',
                dataPlacement: 'right'
                },
            scm_type: {
                label: 'SCM Type',
                type: 'select',
                ngOptions: 'type.label for type in scm_type_options',
                ngChange: 'scmChange()',
                defaultOption: 'Manual',
                addRequired: false, 
                editRequired: false
                },
            missing_path_alert: {
                type: 'alertblock', 
                "class": 'alert-info col-lg-6 col-lg-offset-2', 
                ngShow: 'showMissingPlaybooksAlert && !scm_type',
                alertTxt: '<p class=\"text-justify\"><strong>WARNING:</strong> There are no unassigned playbook directories in the base project path {{ base_dir }}. Either the projects ' +
                    'directory is empty, or all of the contents are already assigned to other projects. New projects can be checked out from source control by ' + 
                    'changing the SCM type option rather than specifying checkout paths manually. To continue with manual setup, log into the AWX server and ' +
                    'ensure content is present in a subdirectory under {{ base_dir }}. Run "chown -R awx" on the content directory to ensure awx can read the ' +
                    'playbooks.</p>'
                },
            base_dir: {
                label: 'Project Base Path',
                type: 'textarea',
                "class": 'col-lg-6',
                showonly: true,
                ngShow: "scm_type == '' || scm_type == null",
                awPopOver: '<p>Base path used for locating playbooks. Directories found inside this path will be listed in the playbook directory drop-down. ' +
                  'Together the base path and selected playbook directory provide the full path used to locate playbooks.</p>' + 
                  '<p>Use PROJECTS_ROOT in your environment settings file to determine the base path value.</p>',
                dataTitle: 'Project Base Path',
                dataContainer: 'body',
                dataPlacement: 'right'
                },
            local_path: {
                label: 'Playbook Directory',
                type: 'select',
                id: 'local-path-select',
                ngOptions: 'path for path in project_local_paths',
                awRequiredWhen: { variable: "pathRequired", init: "true" },
                ngShow: "scm_type == '' || scm_type == null",
                awPopOver: '<p>Select from the list of directories found in the base path.' +
                  'Together the base path and the playbook directory provide the full path used to locate playbooks.</p>' + 
                  '<p>Use PROJECTS_ROOT in your environment settings file to determine the base path value.</p>',
                dataTitle: 'Project Path',
                dataContainer: 'body',
                dataPlacement: 'right'
                },
            scm_url: {
                label: 'SCM URL',
                type: 'text',
                ngShow: "scm_type !== '' && scm_type !== null",
                awValidUrl: true,
                awRequiredWhen: {variable: "scm_type", init: "true" }
                },
            scm_branch: {
                labelBind: "scmBranchLabel",
                type: 'text',
                ngShow: "scm_type !== '' && scm_type !== null",
                addRequired: false,
                editRequired: false
                },
            auth_required: {
                label: 'Authorization required?',
                type: 'checkbox',
                ngShow: "scm_type !== '' && scm_type !== null",
                addRequired: false,
                editRequired: false,
                ngChange: 'authChange()'
                },
            scm_username: {
                label: 'SCM Username',
                type: 'text', 
                ngShow: "scm_type !== '' && scm_type !== null && auth_required",
                addRequired: false, 
                editRequired: false
                },
            "scm_password": {
                label: 'SCM Password',
                type: 'password',
                ngShow: "scm_type !== '' && scm_type !== null && auth_required",
                addRequired: false,
                editRequired: false,
                ngChange: "clearPWConfirm('scm_password_confirm')",
                ask: true,
                clear: true,
                associated: 'scm_password_confirm',
                autocomplete: false
                },
            "scm_password_confirm": {
                label: 'Confirm SCM Password',
                type: 'password',
                ngShow: "scm_type !== '' && scm_type !== null && auth_required",
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'scm_password',
                autocomplete: false
                },
            "scm_key_data": {
                label: 'SCM Private Key',
                type: 'textarea',
                ngShow: "scm_type !== '' && scm_type !== null && auth_required",
                xtraWide: true,
                addRequired: false,
                editRequired: false,
                'class': 'ssh-key-field',
                rows: 10
                },
            "scm_key_unlock": {
                label: 'SCM Key Password',
                type: 'password',
                ngShow: "scm_type !== '' && scm_type !== null && scm_key_data && auth_required",
                addRequired: false,
                editRequired: false,
                ngChange: "clearPWConfirm('scm_key_unlock_confirm')",
                associated: 'scm_key_unlock_confirm',
                ask: true,
                clear: true
                },
            "scm_key_unlock_confirm": {
                label: 'Confirm SCM Key Password',
                type: 'password',
                ngShow: "scm_type !== '' && scm_type !== null && scm_key_data && auth_required",
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'scm_key_unlock'
                },
            checkbox_group: {
                label: 'SCM Options',
                type: 'checkbox_group',
                ngShow: "scm_type !== '' && scm_type !== null",

                fields: [
                    {
                        name: 'scm_clean',
                        label: 'Clean',
                        type: 'checkbox',
                        ngShow: "scm_type !== '' && scm_type !== null",
                        addRequired: false,
                        editRequired: false,
                        awPopOver: '<p>Remove any local modifications prior to performing an update.</p>',
                        dataTitle: 'SCM Clean',
                        dataContainer: 'body',
                        dataPlacement: 'right',
                        labelClass: 'checkbox-options'
                        },
                    {
                        name: 'scm_delete_on_update',
                        label: 'Delete on Update',
                        type: 'checkbox',
                        ngShow: "scm_type !== '' && scm_type !== null",
                        addRequired: false,
                        editRequired: false,
                        awPopOver: '<p>Delete the local repository in its entirety prior to performing an update.</p><p>Depending on the size of the ' +
                           'repository this may significantly increase the amount of time required to complete an update.</p>',
                        dataTitle: 'SCM Delete',
                        dataContainer: 'body',
                        dataPlacement: 'right',
                        labelClass: 'checkbox-options'
                        },
                    {
                        name: 'scm_update_on_launch',
                        label: 'Update on Launch',
                        type: 'checkbox',
                        ngShow: "scm_type !== '' && scm_type !== null",
                        addRequired: false,
                        editRequired: false,
                        awPopOver: '<p>Each time a job runs using this project, perform an update to the local repository prior to starting the job.</p>',
                        dataTitle: 'SCM Update',
                        dataContainer: 'body',
                        dataPlacement: 'right',
                        labelClass: 'checkbox-options'
                        }
                    ]
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
                icon: 'icon-trash',
                'class': 'btn btn-default',
                ngDisabled: true          //Disabled when $pristine
                }
            },

        related: { //related colletions (and maybe items?)
            organizations: {
                type: 'collection',
                title: 'Organizations',
                iterator: 'organization',
                open: false,

                actions: { 
                    add: {
                        ngClick: "add('organizations')",
                        icon: 'icon-plus',
                        label: 'Add',
                        awToolTip: 'Add an organization'
                        }
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
                        label: 'Edit',
                        ngClick: "edit('organizations', \{\{ organization.id \}\}, '\{\{ organization.name \}\}')",
                        icon: 'icon-edit',
                        awToolTip: 'Edit the organization',
                        'class': 'btn btn-default'
                        },
                    "delete": {
                        label: 'Delete',
                        ngClick: "delete('organizations', \{\{ organization.id \}\}, '\{\{ organization.name \}\}', 'organizations')",
                        icon: 'icon-trash',
                        "class": 'btn-danger',
                        awToolTip: 'Delete the organization'
                        }
                    }
                }
            }

    }); // Form

    