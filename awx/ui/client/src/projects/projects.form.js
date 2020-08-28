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

export default ['i18n', 'NotificationsList', 'TemplateList',
 function(i18n, NotificationsList, TemplateList) {
    return function() {
    var projectsFormObj = {
        addTitle: i18n._('NEW PROJECT'),
        editTitle: '{{ name }}',
        name: 'project',
        basePath: 'projects',
        // the top-most node of generated state tree
        stateTree: 'projects',
        forceListeners: true,
        tabs: true,
        subFormTitles: {
            sourceSubForm: i18n._('Source Details'),
        },
        fields: {
            name: {
                label: i18n._('Name'),
                type: 'text',
                ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)',
                required: true,
                capitalize: false
            },
            description: {
                label: i18n._('Description'),
                type: 'text',
                ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            organization: {
                label: i18n._('Organization'),
                type: 'lookup',
                list: 'OrganizationList',
                sourceModel: 'organization',
                basePath: 'organizations',
                sourceField: 'name',
                dataTitle: i18n._('Organization'),
                required: true,
                awPopOver: '<p>' + i18n._('When this project is used by a Job Template, Organization cannot be changed.') + '</p>',
                dataContainer: 'body',
                dataPlacement: 'right',
                ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd) || !canEditOrg',
                awLookupWhen: '(project_obj.summary_fields.user_capabilities.edit || canAdd) && canEditOrg'
            },
            scm_type: {
                label: i18n._('SCM Type'),
                type: 'select',
                class: 'Form-dropDown--scmType',
                defaultText: i18n._('Choose an SCM Type'),
                ngOptions: 'type.label for type in scm_type_options track by type.value',
                ngChange: 'scmChange()',
                required: true,
                hasSubForm: true,
                ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            missing_path_alert: {
                type: 'alertblock',
                ngShow: "showMissingPlaybooksAlert && scm_type.value == 'manual'",
                alertTxt: '<p class=\"text-justify\"><strong>WARNING:</strong> There are no available playbook directories in {{ base_dir }}.  ' +
                    'Either that directory is empty, or all of the contents are already assigned to other projects.  ' +
                    'Create a new directory there and make sure the playbook files can be read by the "awx" system user, ' +
                    'or have {{BRAND_NAME}} directly retrieve your playbooks from source control using the SCM Type option above.</p>',
                closeable: false
            },
            base_dir: {
                label: i18n._('Project Base Path'),
                type: 'text',
                class: 'Form-textUneditable',
                showonly: true,
                ngShow: "scm_type.value == 'manual' " ,
                awPopOver: '<p>' + i18n._('Base path used for locating playbooks. Directories found inside this path will be listed in the playbook directory drop-down. ' +
                    'Together the base path and selected playbook directory provide the full path used to locate playbooks.') + '</p>' +
                    '<p>' + i18n.sprintf(i18n._('Change %s when deploying {{BRAND_NAME}} to change this location.'), 'PROJECTS_ROOT') + '</p>',
                dataTitle: i18n._('Project Base Path'),
                dataContainer: 'body',
                dataPlacement: 'right',
                ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            local_path: {
                label: i18n._('Playbook Directory'),
                type: 'select',
                id: 'local-path-select',
                ngOptions: 'path.label for path in project_local_paths',
                awRequiredWhen: {
                    reqExpression: "pathRequired",
                    init: false
                },
                ngShow: "scm_type.value == 'manual' && !showMissingPlaybooksAlert",
                awPopOver: '<p>' + i18n._('Select from the list of directories found in the Project Base Path. ' +
                    'Together the base path and the playbook directory provide the full path used to locate playbooks.') + '</p>',
                dataTitle: i18n._('Project Path'),
                dataContainer: 'body',
                dataPlacement: 'right',
                ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            scm_url: {
                label: i18n._('SCM URL'),
                type: 'text',
                ngShow: "scm_type && scm_type.value !== 'manual' && scm_type.value !== 'insights' ",
                awRequiredWhen: {
                    reqExpression: "scmRequired",
                    init: false
                },
                subForm: 'sourceSubForm',
                hideSubForm: "scm_type.value === 'manual'",
                awPopOverWatch: "urlPopover",
                awPopOver: "set in controllers/projects",
                dataTitle: i18n._('SCM URL'),
                dataContainer: 'body',
                dataPlacement: 'right',
                ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            scm_branch: {
                labelBind: "scmBranchLabel",
                type: 'text',
                ngShow: "scm_type && scm_type.value !== 'manual' && scm_type.value !== 'insights' && scm_type.value !== 'archive'",
                ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)',
                awPopOver: '<p>' + i18n._("Branch to checkout.  In addition to branches, you can input tags, commit hashes, and arbitrary refs.  Some commit hashes and refs may not be availble unless you also provide a custom refspec.") + '</p>',
                dataTitle: i18n._('SCM Branch'),
                subForm: 'sourceSubForm',
            },
            scm_refspec: {
                labelBind: "scmRefspecLabel",
                type: 'text',
                ngShow: "scm_type && scm_type.value === 'git'",
                ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)',
                awPopOver: '<p>' + i18n._('A refspec to fetch (passed to the Ansible git module).  This parameter allows access to references via the branch field not otherwise available.') + '</p>' +
                    '<p>' + i18n._('NOTE: This field assumes the remote name is "origin".') + '</p>' +
                    '<p>' + i18n._('Examples include:') + '</p>' +
                    '</p><ul class=\"no-bullets\"><li>refs/*:refs/remotes/origin/*</li>' +
                    '<li>refs/pull/62/head:refs/remotes/origin/pull/62/head</li></ul>' +
                    '<p>' + i18n._('The first fetches all references.  The second fetches the Github pull request number 62, in this example the branch needs to be `pull/62/head`.') +
                    '</p>' +
                    '<p>' + i18n._('For more information, refer to the') + '<a target="_blank" href="https://docs.ansible.com/ansible-tower/latest/html/userguide/projects.html#manage-playbooks-using-source-control"> ' + i18n._('Ansible Tower Documentation') + '</a>.</p>',
                dataTitle: i18n._('SCM Refspec'),
                subForm: 'sourceSubForm',
            },
            credential: {
                labelBind: 'credentialLabel',
                type: 'lookup',
                basePath: 'credentials',
                list: 'CredentialList',
                search: {
                    credential_type: null
                },
                ngClick: 'lookupCredential()',
                awRequiredWhen: {
                    reqExpression: "credRequired",
                    init: false
                },
                ngShow: "scm_type && scm_type.value !== 'manual'",
                sourceModel: 'credential',
                awLookupType: '{{lookupType}}',
                sourceField: 'name',
                ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)',
                subForm: 'sourceSubForm'
            },
            checkbox_group: {
                label: i18n._('SCM Update Options'),
                type: 'checkbox_group',
                ngShow: "scm_type && scm_type.value !== 'manual'",
                subForm: 'sourceSubForm',
                fields: [{
                    name: 'scm_clean',
                    label: i18n._('Clean'),
                    type: 'checkbox',
                    awPopOver: '<p>' + i18n._('Remove any local modifications prior to performing an update.') + '</p>',
                    dataTitle: i18n._('SCM Clean'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    labelClass: 'checkbox-options stack-inline',
                    ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)'
                }, {
                    name: 'scm_delete_on_update',
                    label: i18n._('Delete on Update'),
                    type: 'checkbox',
                    awPopOver: '<p>' + i18n._('Delete the local repository in its entirety prior to performing an update.') + '</p><p>' + i18n._('Depending on the size of the ' +
                        'repository this may significantly increase the amount of time required to complete an update.') + '</p>',
                    dataTitle: i18n._('SCM Delete'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    labelClass: 'checkbox-options stack-inline',
                    ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)'
                }, {
                    name: 'scm_update_on_launch',
                    label: i18n._('Update Revision on Launch'),
                    type: 'checkbox',
                    awPopOver: '<p>' + i18n._('Each time a job runs using this project, update the revision of the project prior to starting the job.') + '</p>',
                    dataTitle: i18n._('SCM Update'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    labelClass: 'checkbox-options stack-inline',
                    ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                {
                    name: 'allow_override',
                    label: i18n._('Allow branch override'),
                    type: 'checkbox',
                    awPopOver: '<p>' + i18n._('Allow changing the SCM branch or revision in a job template that uses this project.') + '</p>',
                    dataTitle: i18n._('Allow branch override'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    labelClass: 'checkbox-options stack-inline',
                    ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)',
                    ngShow: "scm_type && scm_type.value !== 'insights'",
                }]
            },
            scm_update_cache_timeout: {
                label: i18n.sprintf(i18n._('Cache Timeout%s (seconds)%s'), '<span class="small-text">', '</span>'),
                id: 'scm-cache-timeout',
                type: 'number',
                integer: true,
                min: 0,
                ngShow: "scm_update_on_launch && scm_type.value !== 'manual'",
                spinner: true,
                "default": '0',
                awPopOver: '<p>' + i18n._('Time in seconds to consider a project to be current. During job runs and callbacks the task system will ' +
                    'evaluate the timestamp of the latest project update. If it is older than Cache Timeout, it is not considered current, ' +
                    'and a new project update will be performed.') + '</p>',
                dataTitle: i18n._('Cache Timeout'),
                dataPlacement: 'right',
                dataContainer: "body",
                ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)',
                subForm: 'sourceSubForm'
            },
            custom_virtualenv: {
                label: i18n._('Ansible Environment'),
                type: 'select',
                defaultText: i18n._('Use Default Environment'),
                ngOptions: 'venv for venv in custom_virtualenvs_options track by venv',
                awPopOver: "<p>" + i18n._("Select the custom Python virtual environment for this project to run on.") + "</p>",
                dataTitle: i18n._('Ansible Environment'),
                dataContainer: 'body',
                dataPlacement: 'right',
                ngDisabled: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)',
                ngShow: 'custom_virtualenvs_options.length > 1'
            },
        },

        buttons: {
            cancel: {
                ngClick: 'formCancel()',
                ngShow: '(project_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            close: {
                ngClick: 'formCancel()',
                ngShow: '!(project_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            save: {
                ngClick: 'formSave()',
                ngDisabled: true,
                ngShow: '(project_obj.summary_fields.user_capabilities.edit || canAdd)'
            }
        },

        related: {
            permissions: {
                name: 'permissions',
                awToolTip: i18n._('Please save before assigning permissions.'),
                djangoModel: 'access_list',
                dataPlacement: 'top',
                basePath: 'api/v2/projects/{{$stateParams.project_id}}/access_list/',
                search: {
                    order_by: 'username'
                },
                type: 'collection',
                title: i18n._('Permissions'),
                iterator: 'permission',
                index: false,
                open: false,
                actions: {
                    add: {
                        ngClick: "$state.go('.add')",
                        label: i18n._('Add'),
                        awToolTip: i18n._('Add a permission'),
                        actionClass: 'at-Button--add',
                        actionId: 'button-add--permission',
                        ngShow: '(project_obj.summary_fields.user_capabilities.edit || canAdd)'
                    }
                },

                fields: {
                    username: {
                        key: true,
                        label: i18n._('User'),
                        linkBase: 'users',
                        columnClass: 'col-sm-3 col-xs-4'
                    },
                    role: {
                        label: i18n._('Role'),
                        type: 'role',
                        nosort: true,
                        columnClass: 'col-sm-4 col-xs-4',
                    },
                    team_roles: {
                        label: i18n._('Team Roles'),
                        type: 'team_roles',
                        nosort: true,
                        columnClass: 'col-sm-5 col-xs-4',
                    }
                }
            },
            notifications: {
                include: "NotificationsList",
            },
            templates: {
                include: "TemplateList",
            },
            schedules: {
                title: i18n._('Schedules'),
                skipGenerator: true,
                ngClick: "$state.go('projects.edit.schedules')"
            }
        }

    };

    var itm;

    for (itm in projectsFormObj.related) {
        if (projectsFormObj.related[itm].include === "TemplateList") {
            projectsFormObj.related[itm] = _.clone(TemplateList);
            projectsFormObj.related[itm].title = i18n._('Job Templates');
            projectsFormObj.related[itm].skipGenerator = true;
        }
        if (projectsFormObj.related[itm].include === "NotificationsList") {
            projectsFormObj.related[itm] = NotificationsList;
            projectsFormObj.related[itm].generateList = true;   // tell form generator to call list generator and inject a list
        }
    }
    return projectsFormObj;
};}];
