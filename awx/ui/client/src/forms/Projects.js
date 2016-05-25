/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

  /**
 * @ngdoc function
 * @name forms.function:Projects
 * @description This form is for adding/editing projects
*/

export default
angular.module('ProjectFormDefinition', ['SchedulesListDefinition'])
    .value('ProjectsFormObject', {

        addTitle: 'New Project',
        editTitle: '{{ name }}',
        name: 'project',
        forceListeners: true,
        tabs: true,
        subFormTitles: {
            sourceSubForm: 'Source Details',
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
                ngClick: 'lookUpOrganization()',
                awRequiredWhen: {
                    reqExpression: "organizationrequired",
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
                class: 'Form-dropDown--scmType',
                ngOptions: 'type.label for type in scm_type_options track by type.value',
                ngChange: 'scmChange()',
                addRequired: true,
                editRequired: true,
                hasSubForm: true
            },
            missing_path_alert: {
                type: 'alertblock',
                "class": 'alert-info',
                ngShow: "showMissingPlaybooksAlert && scm_type.value == 'manual'",
                alertTxt: '<p class=\"text-justify\"><strong>WARNING:</strong> There are no available playbook directories in {{ base_dir }}.  ' +
                    'Either that directory is empty, or all of the contents are already assigned to other projects.  ' +
                    'Create a new directory there and make sure the playbook files can be read by the "awx" system user, ' +
                    'or have Tower directly retrieve your playbooks from source control using the SCM Type option above.</p>',
                closeable: false
            },
            base_dir: {
                label: 'Project Base Path',
                type: 'text',
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
                    reqExpression: "pathRequired",
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
                    reqExpression: "scmRequired",
                    init: false
                },
                subForm: 'sourceSubForm',
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
                }],
            },
            scm_branch: {
                labelBind: "scmBranchLabel",
                type: 'text',
                ngShow: "scm_type && scm_type.value !== 'manual'",
                addRequired: false,
                editRequired: false,
                subForm: 'sourceSubForm'
            },
            credential: {
                label: 'SCM Credential',
                type: 'lookup',
                ngShow: "scm_type && scm_type.value !== 'manual'",
                sourceModel: 'credential',
                sourceField: 'name',
                ngClick: 'lookUpCredential()',
                addRequired: false,
                editRequired: false,
                subForm: 'sourceSubForm'
            },
            checkbox_group: {
                label: 'SCM Update Options',
                type: 'checkbox_group',
                ngShow: "scm_type && scm_type.value !== 'manual'",
                subForm: 'sourceSubForm',
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
                    labelClass: 'checkbox-options stack-inline'
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
                    labelClass: 'checkbox-options stack-inline'
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
                    labelClass: 'checkbox-options stack-inline'
                }]
            },
            scm_update_cache_timeout: {
                label: 'Cache Timeout<span class=\"small-text\"> (seconds)</span>',
                id: 'scm-cache-timeout',
                type: 'number',
                integer: true,
                min: 0,
                ngShow: "scm_update_on_launch && projectSelected",
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
            cancel: {
                ngClick: 'formCancel()'
            },
            save: {
                ngClick: 'formSave()',
                ngDisabled: true
            }
        },

        related: {
            permissions: {
                awToolTip: 'Please save before assigning permissions',
                dataPlacement: 'top',
                basePath: 'projects/:id/access_list/',
                type: 'collection',
                title: 'Permissions',
                iterator: 'permission',
                index: false,
                open: false,
                searchType: 'select',
                actions: {
                    add: {
                        ngClick: "addPermission",
                        label: 'Add',
                        awToolTip: 'Add a permission',
                        actionClass: 'btn List-buttonSubmit',
                        buttonContent: '&#43; ADD'
                    }
                },

                fields: {
                    username: {
                        key: true,
                        label: 'User',
                        linkBase: 'users',
                        class: 'col-lg-3 col-md-3 col-sm-3 col-xs-4'
                    },
                    role: {
                        label: 'Role',
                        type: 'role',
                        noSort: true,
                        class: 'col-lg-4 col-md-4 col-sm-4 col-xs-4'
                    },
                    team_roles: {
                        label: 'Team Roles',
                        type: 'team_roles',
                        noSort: true,
                        class: 'col-lg-5 col-md-5 col-sm-5 col-xs-4'
                    }
                }
            },
            notifications: {
                include: "NotificationsList",
            }
        },

        relatedSets: function(urls) {
            return {
                permissions: {
                    iterator: 'permission',
                    url: urls.access_list
                },
                notifications: {
                    iterator: 'notification',
                    url: '/api/v1/notification_templates/'
                }
            };
        }

    })

    .factory('ProjectsForm', ['ProjectsFormObject', 'NotificationsList', function(ProjectsFormObject, NotificationsList) {
        return function() {
            var itm;
            for (itm in ProjectsFormObject.related) {
                if (ProjectsFormObject.related[itm].include === "NotificationsList") {
                    ProjectsFormObject.related[itm] = NotificationsList;
                    ProjectsFormObject.related[itm].generateList = true;   // tell form generator to call list generator and inject a list
                }
            }
            return ProjectsFormObject;
        };
    }]);
