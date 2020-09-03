/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$stateParams', 'ProjectsForm', 'Rest',
    'Alert', 'ProcessErrors', 'GenerateForm', 'Prompt', 'isNotificationAdmin',
    'GetBasePath', 'GetProjectPath', 'Authorization', 'GetChoices', 'Empty',
    'Wait', 'ProjectUpdate', '$state', 'CreateSelect2', 'ToggleNotification',
    'i18n', 'OrgAdminLookup', 'ConfigData', 'scmCredentialType', 'insightsCredentialType',
    function($scope, $rootScope, $stateParams, ProjectsForm, Rest, Alert,
    ProcessErrors, GenerateForm, Prompt, isNotificationAdmin, GetBasePath,
    GetProjectPath, Authorization, GetChoices, Empty, Wait, ProjectUpdate,
    $state, CreateSelect2, ToggleNotification, i18n, OrgAdminLookup,
    ConfigData, scmCredentialType, insightsCredentialType) {

        let form = ProjectsForm(),
            defaultUrl = GetBasePath('projects') + $stateParams.project_id + '/',
            main = {},
            id = $stateParams.project_id;

        $scope.project_local_paths = [];
        $scope.base_dir = '';
        const virtualEnvs = ConfigData.custom_virtualenvs || [];
        $scope.custom_virtualenvs_options = virtualEnvs;

        $scope.$watch('project_obj.summary_fields.user_capabilities.edit', function(val) {
            if (val === false) {
                $scope.canAdd = false;
            }
        });

        if ($scope.pathsReadyRemove) {
            $scope.pathsReadyRemove();
        }
        $scope.pathsReadyRemove = $scope.$on('pathsReady', function () {
            CreateSelect2({
                element: '#local-path-select',
                multiple: false
            });
        });

        // After the project is loaded, retrieve each related set
        if ($scope.projectLoadedRemove) {
            $scope.projectLoadedRemove();
        }
        $scope.projectLoadedRemove = $scope.$on('projectLoaded', function() {
            GetProjectPath({ scope: $scope, main: main });

            $scope.pathRequired = ($scope.scm_type.value === 'manual') ? true : false;
            $scope.scmRequired = ($scope.scm_type.value !== 'manual') ? true : false;
            $scope.scmBranchLabel = ($scope.scm_type.value === 'svn') ? 'Revision #' : 'SCM Branch';
            Wait('stop');

            $scope.scmChange();
        });

        if ($scope.removeChoicesReady) {
            $scope.removeChoicesReady();
        }
        $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
            let i;
            for (i = 0; i < $scope.scm_type_options.length; i++) {
                if ($scope.scm_type_options[i].value === '') {
                    $scope.scm_type_options[i].value = "manual";
                    break;
                }
            }
            // Retrieve detail record and prepopulate the form
            Rest.setUrl(defaultUrl);
            Rest.get({ params: { id: id } })
                .then(({data}) => {
                    var fld, i;
                    for (fld in form.fields) {
                        if (form.fields[fld].type === 'checkbox_group') {
                            for (i = 0; i < form.fields[fld].fields.length; i++) {
                                $scope[form.fields[fld].fields[i].name] = data[form.fields[fld].fields[i].name];
                                main[form.fields[fld].fields[i].name] = data[form.fields[fld].fields[i].name];
                            }
                        } else {
                            if (data[fld] !== undefined) {
                                $scope[fld] = data[fld];
                                main[fld] = data[fld];
                            }
                        }
                        if (form.fields[fld].sourceModel && data.summary_fields &&
                            data.summary_fields[form.fields[fld].sourceModel]) {
                            $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                            main[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                        }
                    }

                    data.scm_type = (Empty(data.scm_type)) ? 'manual' : data.scm_type;
                    for (i = 0; i < $scope.scm_type_options.length; i++) {
                        if ($scope.scm_type_options[i].value === data.scm_type) {
                            $scope.scm_type = $scope.scm_type_options[i];
                            break;
                        }
                    }

                    if ($scope.scm_type.value !== 'manual') {
                        $scope.pathRequired = false;
                        $scope.scmRequired = true;
                    } else {
                        $scope.pathRequired = true;
                        $scope.scmRequired = false;
                    }

                    main.scm_type = $scope.scm_type;
                    CreateSelect2({
                        element: '#project_scm_type',
                        multiple: false
                    });

                    $scope.scmBranchLabel = ($scope.scm_type.value === 'svn') ? 'Revision #' : 'SCM Branch';
                    $scope.scm_update_tooltip = i18n._("Get latest SCM revision");
                    $scope.scm_type_class = "";
                    if (data.status === 'running' || data.status === 'updating') {
                        $scope.scm_update_tooltip = i18n._("SCM update currently running");
                        $scope.scm_type_class = "btn-disabled";
                    }
                    if (Empty(data.scm_type)) {
                        $scope.scm_update_tooltip = i18n._('Manual projects do not require an SCM update');
                        $scope.scm_type_class = "btn-disabled";
                    }

                    OrgAdminLookup.checkForRoleLevelAdminAccess(data.organization, 'project_admin_role')
                    .then(function(canEditOrg){
                        $scope.canEditOrg = canEditOrg;
                    });

                    CreateSelect2({
                        element: '#project_custom_virtualenv',
                        multiple: false,
                        opts: $scope.custom_virtualenvs_options
                    });

                    $scope.project_obj = data;
                    // To toggle notifications a user needs to have an admin role on the project
                    // _and_ have at least a notification template admin role on an org.
                    // Only users with admin role on the project can edit it which is why we
                    // look at that user_capability
                    $scope.sufficientRoleForNotifToggle = isNotificationAdmin && data.summary_fields.user_capabilities.edit;
                    $scope.sufficientRoleForNotif =  isNotificationAdmin || $scope.user_is_system_auditor;
                    $scope.name = data.name;
                    $scope.breadcrumb.project_name = data.name;
                    $scope.$emit('projectLoaded');
                    Wait('stop');
                })
                .catch(({data, status}) => {
                    ProcessErrors($scope, data, status, form, { hdr: i18n._('Error!'),
                        msg: i18n.sprintf(i18n._('Failed to retrieve project: %s. GET status: '), id) + status
                    });
                });
        });

        // Load the list of options for Kind
        Wait('start');
        GetChoices({
            url: GetBasePath('projects'),
            scope: $scope,
            field: 'scm_type',
            variable: 'scm_type_options',
            callback: 'choicesReady'
        });

        $scope.toggleNotification = function(event, id, column) {
            var notifier = this.notification;
            try {
                $(event.target).tooltip('hide');
            } catch (e) {
                // ignore
            }
            ToggleNotification({
                scope: $scope,
                url: $scope.project_obj.url,
                notifier: notifier,
                column: column,
                callback: 'NotificationRefresh'
            });
        };

        // Save changes to the parent
        $scope.formSave = function() {
            var fld, i, params;
            GenerateForm.clearApiErrors($scope);
            Wait('start');
            $rootScope.flashMessage = null;
            params = {};
            for (fld in form.fields) {
                if (form.fields[fld].type === 'checkbox_group') {
                    for (i = 0; i < form.fields[fld].fields.length; i++) {
                        params[form.fields[fld].fields[i].name] = $scope[form.fields[fld].fields[i].name];
                    }
                } else {
                    if (form.fields[fld].type !== 'alertblock') {
                        params[fld] = $scope[fld];
                    }
                }
            }

            if ($scope.scm_type.value === "manual") {
                params.scm_type = "";
                params.local_path = $scope.local_path.value;
            } else {
                params.scm_type = $scope.scm_type.value;
                delete params.local_path;
            }

            Rest.setUrl(defaultUrl);
            Rest.put(params)
                .then(() => {
                    Wait('stop');
                    $state.go($state.current, {}, { reload: true });
                })
                .catch(({data, status}) => {
                    ProcessErrors($scope, data, status, form, { hdr: i18n._('Error!'), msg: i18n.sprintf(i18n._('Failed to update project: %s. PUT status: '), id) + status });
                });
        };

        // Related set: Delete button
        $scope['delete'] = function(set, itm_id, name, title) {
            var action = function() {
                var url = GetBasePath('projects') + id + '/' + set + '/';
                $rootScope.flashMessage = null;
                Rest.setUrl(url);
                Rest.post({ id: itm_id, disassociate: 1 })
                    .then(() => {
                        $('#prompt-modal').modal('hide');
                    })
                    .catch(({data, status}) => {
                        $('#prompt-modal').modal('hide');
                        ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'), msg: i18n.sprintf(i18n._('Call to %s failed. POST returned status: '), url) + status });
                    });
            };

            Prompt({
                hdr: i18n._('Delete'),
                body: '<div class="Prompt-bodyQuery">' + i18n.sprintf(i18n._('Are you sure you want to remove the %s below from %s?'), title, $scope.name) + '</div>' + '<div class="Prompt-bodyTarget">' + name + '</div>',
                action: action,
                actionText: i18n._('DELETE')
            });
        };

        $scope.scmChange = function() {
            if ($scope.scm_type) {
                $scope.pathRequired = ($scope.scm_type.value === 'manual') ? true : false;
                $scope.scmRequired = ($scope.scm_type.value !== 'manual') ? true : false;
                $scope.scmBranchLabel = i18n._('SCM Branch');
                $scope.scmRefspecLabel = i18n._('SCM Refspec');

                // Dynamically update popover values
                if ($scope.scm_type.value) {
                    if(($scope.lookupType === 'insights_credential' && $scope.scm_type.value !== 'insights') || ($scope.lookupType === 'scm_credential' && $scope.scm_type.value === 'insights')) {
                        $scope.credential = null;
                        $scope.credential_name = '';
                    }
                    switch ($scope.scm_type.value) {
                        case 'git':
                            $scope.credentialLabel = "SCM " + i18n._("Credential");
                            $scope.urlPopover = '<p>' + i18n._('Example URLs for GIT SCM include:') + '</p><ul class=\"no-bullets\"><li>https://github.com/ansible/ansible.git</li>' +
                                '<li>git@github.com:ansible/ansible.git</li><li>git://servername.example.com/ansible.git</li></ul>' +
                                '<p>' + i18n.sprintf(i18n._('%sNote:%s When using SSH protocol for GitHub or Bitbucket, enter an SSH key only, ' +
                                'do not enter a username (other than git). Additionally, GitHub and Bitbucket do not support password authentication when using ' +
                                'SSH. GIT read only protocol (git://) does not use username or password information.'), '<strong>', '</strong>');
                            $scope.credRequired = false;
                            $scope.lookupType = 'scm_credential';
                            $scope.scmBranchLabel = i18n._('SCM Branch/Tag/Commit');
                            break;
                        case 'svn':
                            $scope.credentialLabel = "SCM " + i18n._("Credential");
                            $scope.urlPopover = '<p>' + i18n._('Example URLs for Subversion SCM include:') + '</p>' +
                                '<ul class=\"no-bullets\"><li>https://github.com/ansible/ansible</li><li>svn://servername.example.com/path</li>' +
                                '<li>svn+ssh://servername.example.com/path</li></ul>';
                            $scope.credRequired = false;
                            $scope.lookupType = 'scm_credential';
                            $scope.scmBranchLabel = i18n._('Revision #');
                            break;
                        case 'hg':
                            $scope.credentialLabel = "SCM " + i18n._("Credential");
                            $scope.urlPopover = '<p>' + i18n._('Example URLs for Mercurial SCM include:') + '</p>' +
                                '<ul class=\"no-bullets\"><li>https://bitbucket.org/username/project</li><li>ssh://hg@bitbucket.org/username/project</li>' +
                                '<li>ssh://server.example.com/path</li></ul>' +
                                '<p>' + i18n.sprintf(i18n._('%sNote:%s Mercurial does not support password authentication for SSH. ' +
                                'Do not put the username and key in the URL. ' +
                                'If using Bitbucket and SSH, do not supply your Bitbucket username.'), '<strong>', '</strong>');
                            $scope.credRequired = false;
                            $scope.lookupType = 'scm_credential';
                            $scope.scmBranchLabel = i18n._('SCM Branch/Tag/Revision');
                            break;
                        case 'archive':
                            $scope.credentialLabel = "SCM " + i18n._("Credential");
                            $scope.urlPopover = '<p>' + i18n._('Example URLs for Remote Archive SCM include:') + '</p>' +
                                '<ul class=\"no-bullets\"><li>https://github.com/username/project/archive/v0.0.1.tar.gz</li>' +
                                '<li>http://github.com/username/project/archive/v0.0.2.zip</li></ul>';
                            $scope.credRequired = false;
                            $scope.lookupType = 'scm_credential';
                            break;
                        case 'insights':
                            $scope.pathRequired = false;
                            $scope.scmRequired = false;
                            $scope.credRequired = true;
                            $scope.credentialLabel = "Credential";
                            $scope.lookupType = 'insights_credential';
                            break;
                        default:
                            $scope.credentialLabel = "SCM " + i18n._("Credential");
                            $scope.urlPopover = '<p> ' + i18n._('URL popover text');
                            $scope.credRequired = false;
                            $scope.lookupType = 'scm_credential';
                    }
                }
            }
        };

        $scope.lookupCredential = function(){
            // Perform a lookup on the credential_type. Git, Mercurial, and Subversion
            // all use SCM as their credential type.
            let lookupCredentialType = scmCredentialType;
            if ($scope.scm_type.value === 'insights') {
                lookupCredentialType = insightsCredentialType;
            }
            $state.go('.credential', {
                credential_search: {
                    credential_type: lookupCredentialType,
                    page_size: '5',
                    page: '1'
                }
            });
        };

        $scope.SCMUpdate = function() {
            if ($scope.project_obj.scm_type === "Manual" || Empty($scope.project_obj.scm_type)) {
                // ignore
            } else if ($scope.project_obj.status === 'updating' || $scope.project_obj.status === 'running' || $scope.project_obj.status === 'pending') {
                Alert(i18n._('Update in Progress'), i18n._('The SCM update process is running.'), 'alert-info');
            } else {
                ProjectUpdate({ scope: $scope, project_id: $scope.project_obj.id });
            }
        };

        $scope.formCancel = function() {
            $state.transitionTo('projects');
        };
    }
];
