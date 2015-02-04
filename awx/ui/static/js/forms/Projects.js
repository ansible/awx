/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Projects.js
 *
 *  Form definition for Projects model
 *
 *
 */
  /**
 * @ngdoc function
 * @name forms.function:Projects
 * @description This form is for adding/editing projects
*/
angular.module('ProjectFormDefinition', ['SchedulesListDefinition'])
    .value('ProjectsFormObject', {

        addTitle: 'Create Project',
        editTitle: '{{ name }}',
        name: 'project',
        forceListeners: true,
        well: true,
        collapse: true,
        collapseTitle: "Properties",
        collapseMode: 'edit',
        collapseOpen: true,

        actions: {
            // scm_update: {
            //     mode: 'edit',
            //     ngClick: 'SCMUpdate()',
            //     awToolTip: "{{ scm_update_tooltip }}",
            //     dataTipWatch: "scm_update_tooltip",
            //     ngClass: "scm_type_class",
            //     dataPlacement: 'top',
            //     ngDisabled: "scm_type.value === 'manual' "
            // },
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
                capitalize: false
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
                awRequiredWhen: {
                    variable: "organizationrequired",
                    init: "true"
                },
                awPopOver: '<p>A project must have at least one organization. Pick one organization now to create the project, and then after ' +
                    'the project is created you can add additional organizations.</p><p>Only super users and organization administrators are allowed ' +
                    'to make changes to projects. Associating one or more organizations to a project determins which organizations admins have ' +
                    'access to modify the project.',
                dataTitle: 'Organization',
                dataContainer: 'body',
                dataPlacement: 'right'
            },
            scm_type: {
                label: 'SCM Type',
                type: 'select',
                ngOptions: 'type.label for type in scm_type_options track by type.value',
                ngChange: 'scmChange()',
                addRequired: true,
                editRequired: true
            },
            missing_path_alert: {
                type: 'alertblock',
                "class": 'alert-info',
                ngShow: "showMissingPlaybooksAlert && scm_type.value == 'manual'",
                alertTxt: '<p class=\"text-justify\"><strong>WARNING:</strong> There are no unassigned playbook directories in the base ' +
                    'project path {{ base_dir }}. Either the projects directory is empty, or all of the contents are already assigned to ' +
                    'other projects. New projects can be checked out from source control by ' +
                    'changing the SCM type option rather than specifying checkout paths manually. To continue with manual setup, log into ' +
                    'the Tower host and ensure content is present in a subdirectory under {{ base_dir }}. Run "chown -R awx" on the content ' +
                    'directory to ensure Tower can read the playbooks.</p>',
                closeable: false
            },
            base_dir: {
                label: 'Project Base Path',
                type: 'textarea',
                //"class": 'col-lg-6',
                showonly: true,
                ngShow: "scm_type.value == 'manual' " ,
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
                ngOptions: 'path.label for path in project_local_paths',
                awRequiredWhen: {
                    variable: "pathRequired",
                    init: false
                },
                ngShow: "scm_type.value == 'manual' && !showMissingPlaybooksAlert",
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
                ngShow: "scm_type && scm_type.value !== 'manual'",
                awRequiredWhen: {
                    variable: "scmRequired",
                    init: false
                },
                helpCollapse: [{
                    hdr: 'GIT URLs',
                    content: '<p>Example URLs for GIT SCM include:</p><ul class=\"no-bullets\"><li>https://github.com/ansible/ansible.git</li>' +
                        '<li>git@github.com:ansible/ansible.git</li><li>git://servername.example.com/ansible.git</li></ul>' +
                        '<p><strong>Note:</strong> When using SSH protocol for GitHub or Bitbucket, enter an SSH key only, ' +
                        'do not enter a username (other than git). Additionally, GitHub and Bitbucket do not support password authentication when using ' +
                        'SSH. GIT read only protocol (git://) does not use username or password information.',
                    show: "scm_type.value == 'git'"
                }, {
                    hdr: 'SVN URLs',
                    content: '<p>Example URLs for Subversion SCM include:</p>' +
                        '<ul class=\"no-bullets\"><li>https://github.com/ansible/ansible</li><li>svn://servername.example.com/path</li>' +
                        '<li>svn+ssh://servername.example.com/path</li></ul>',
                    show: "scm_type.value == 'svn'"
                }, {
                    hdr: 'Mercurial URLs',
                    content: '<p>Example URLs for Mercurial SCM include:</p>' +
                        '<ul class=\"no-bullets\"><li>https://bitbucket.org/username/project</li><li>ssh://hg@bitbucket.org/username/project</li>' +
                        '<li>ssh://server.example.com/path</li></ul>' +
                        '<p><strong>Note:</strong> Mercurial does not support password authentication for SSH. ' +
                        'Do not put the username and key in the URL. ' +
                        'If using Bitbucket and SSH, do not supply your Bitbucket username.',
                    show: "scm_type.value == 'hg'"
                }]
            },
            scm_branch: {
                labelBind: "scmBranchLabel",
                type: 'text',
                ngShow: "scm_type && scm_type.value !== 'manual'",
                addRequired: false,
                editRequired: false
            },
            credential: {
                label: 'SCM Credential',
                type: 'lookup',
                ngShow: "scm_type && scm_type.value !== 'manual'",
                sourceModel: 'credential',
                sourceField: 'name',
                ngClick: 'lookUpCredential()',
                addRequired: false,
                editRequired: false
            },
            checkbox_group: {
                label: 'SCM Update Options',
                type: 'checkbox_group',
                ngShow: "scm_type && scm_type.value !== 'manual'",
                fields: [{
                    name: 'scm_clean',
                    label: 'Clean',
                    type: 'checkbox',
                    addRequired: false,
                    editRequired: false,
                    awPopOver: '<p>Remove any local modifications prior to performing an update.</p>',
                    dataTitle: 'SCM Clean',
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    labelClass: 'checkbox-options'
                }, {
                    name: 'scm_delete_on_update',
                    label: 'Delete on Update',
                    type: 'checkbox',
                    addRequired: false,
                    editRequired: false,
                    awPopOver: '<p>Delete the local repository in its entirety prior to performing an update.</p><p>Depending on the size of the ' +
                        'repository this may significantly increase the amount of time required to complete an update.</p>',
                    dataTitle: 'SCM Delete',
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    labelClass: 'checkbox-options'
                }, {
                    name: 'scm_update_on_launch',
                    label: 'Update on Launch',
                    type: 'checkbox',
                    addRequired: false,
                    editRequired: false,
                    awPopOver: '<p>Each time a job runs using this project, perform an update to the local repository prior to starting the job.</p>',
                    dataTitle: 'SCM Update',
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    labelClass: 'checkbox-options'
                }]
            },
            scm_update_cache_timeout: {
                label: 'Cache Timeout',
                id: 'scm-cache-timeout',
                type: 'number',
                integer: true,
                min: 0,
                ngShow: "scm_update_on_launch",
                spinner: true,
                "default": '0',
                addRequired: false,
                editRequired: false,
                awPopOver: '<p>Time in seconds to consider a project to be current. During job runs and callbacks the task system will ' +
                    'evaluate the timestamp of the latest project update. If it is older than Cache Timeout, it is not considered current, ' +
                    'and a new project update will be performed.</p>',
                dataTitle: 'Cache Timeout',
                dataPlacement: 'right',
                dataContainer: "body"
            }
        },

        buttons: {
            save: {
                ngClick: 'formSave()',
                ngDisabled: true
            },
            reset: {
                ngClick: 'formReset()',
                ngDisabled: true
            }
        },

        related: {
            organizations: {
                type: 'collection',
                title: 'Organizations',
                iterator: 'organization',
                index: false,
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
                        ngClick: "edit('organizations', organization.id, organization.name)",
                        icon: 'icon-edit',
                        awToolTip: 'Edit the organization',
                        'class': 'btn btn-default'
                    },
                    "delete": {
                        label: 'Delete',
                        ngClick: "delete('organizations', organization.id, organization.name, 'organizations')",
                        icon: 'icon-trash',
                        "class": 'btn-danger',
                        awToolTip: 'Delete the organization'
                    }
                }
            },

            schedules: {
                include: "SchedulesList",
                index: false
            }

        },

        relatedSets: function(urls) {
            return {
                organizations: {
                    iterator: 'organization',
                    url: urls.organizations
                },
                schedules: {
                    iterator: 'schedule',
                    url: urls.schedules
                }
            };
        }

    })

    .factory('ProjectsForm', ['ProjectsFormObject', 'SchedulesList', function(ProjectsFormObject, ScheduleList) {
        return function() {
            var itm;
            for (itm in ProjectsFormObject.related) {
                if (ProjectsFormObject.related[itm].include === "SchedulesList") {
                    ProjectsFormObject.related[itm] = ScheduleList;
                    ProjectsFormObject.related[itm].generateList = true;   // tell form generator to call list generator and inject a list
                }
            }
            return ProjectsFormObject;
        };
    }]);