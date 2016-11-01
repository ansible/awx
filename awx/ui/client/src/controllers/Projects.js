/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Projects
 * @description This controller's for the projects page
 */


export function ProjectsList($scope, $rootScope, $location, $log, $stateParams,
    Rest, Alert, ProjectList, Prompt, ReturnToCaller, ClearScope, ProcessErrors,
    GetBasePath, ProjectUpdate, Wait, GetChoices, Empty, Find, GetProjectIcon,
    GetProjectToolTip, $filter, $state, rbacUiControlService, Dataset, i18n) {

    var list = ProjectList,
        defaultUrl = GetBasePath('projects');

    init();

    function init() {
        $scope.canAdd = false;

        rbacUiControlService.canAdd('projects')
            .then(function(canAdd) {
                $scope.canAdd = canAdd;
            });

        // search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        _.forEach($scope[list.name], buildTooltips);
        $rootScope.flashMessage = null;
    }

    $scope.$watch(`${list.name}`, function() {
        _.forEach($scope[list.name], buildTooltips);
    });

    function buildTooltips(project) {
        project.statusIcon = GetProjectIcon(project.status);
        project.statusTip = GetProjectToolTip(project.status);
        project.scm_update_tooltip = "Start an SCM update";
        project.scm_schedule_tooltip = i18n._("Schedule future SCM updates");
        project.scm_type_class = "";

        if (project.status === 'failed' && project.summary_fields.last_update && project.summary_fields.last_update.status === 'canceled') {
            project.statusTip = i18n._('Canceled. Click for details');
        }

        if (project.status === 'running' || project.status === 'updating') {
            project.scm_update_tooltip = i18n._("SCM update currently running");
            project.scm_type_class = "btn-disabled";
        }
        if (project.scm_type === 'manual') {
            project.scm_update_tooltip = i18n._('Manual projects do not require an SCM update');
            project.scm_schedule_tooltip = i18n._('Manual projects do not require a schedule');
            project.scm_type_class = 'btn-disabled';
            project.statusTip = i18n._('Not configured for SCM');
            project.statusIcon = 'none';
        }
    }

    $scope.$on(`ws-jobs`, function(e, data) {
        var project;
        $log.debug(data);
        if ($scope.projects) {
            // Assuming we have a list of projects available
            project = Find({ list: $scope.projects, key: 'id', val: data.project_id });
            if (project) {
                // And we found the affected project
                $log.debug('Received event for project: ' + project.name);
                $log.debug('Status changed to: ' + data.status);
                if (data.status === 'successful' || data.status === 'failed') {
                    // @issue: OLD SEARCH
                    // $scope.search(list.iterator, null, null, null, null, false);
                } else {
                    project.scm_update_tooltip = "SCM update currently running";
                    project.scm_type_class = "btn-disabled";
                }
                project.status = data.status;
                project.statusIcon = GetProjectIcon(data.status);
                project.statusTip = GetProjectToolTip(data.status);
            }
        }
    });

    $scope.addProject = function() {
        $state.go('projects.add');
    };

    $scope.editProject = function(id) {
        $state.go('projects.edit', { project_id: id });
    };

    if ($scope.removeGoToJobDetails) {
        $scope.removeGoToJobDetails();
    }
    $scope.removeGoToJobDetails = $scope.$on('GoToJobDetails', function(e, data) {
        if (data.summary_fields.current_update || data.summary_fields.last_update) {

            Wait('start');

            // Grab the id from summary_fields
            var id = (data.summary_fields.current_update) ? data.summary_fields.current_update.id : data.summary_fields.last_update.id;

            $state.go('scmUpdateStdout', { id: id });

        } else {
            Alert(i18n._('No Updates Available'), i18n._('There is no SCM update information available for this project. An update has not yet been ' +
                ' completed.  If you have not already done so, start an update for this project.'), 'alert-info');
        }
    });

    $scope.showSCMStatus = function(id) {
        // Refresh the project list
        var project = Find({ list: $scope.projects, key: 'id', val: id });
        if (Empty(project.scm_type) || project.scm_type === 'Manual') {
            Alert(i18n._('No SCM Configuration'), i18n._('The selected project is not configured for SCM. To configure for SCM, edit the project and provide SCM settings, ' +
                'and then run an update.'), 'alert-info');
        } else {
            // Refresh what we have in memory to insure we're accessing the most recent status record
            Rest.setUrl(project.url);
            Rest.get()
                .success(function(data) {
                    $scope.$emit('GoToJobDetails', data);
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'),
                        msg: i18n._('Project lookup failed. GET returned: ') + status });
                });
        }
    };

    $scope.deleteProject = function(id, name) {
        var action = function() {
            $('#prompt-modal').modal('hide');
            Wait('start');
            var url = defaultUrl + id + '/';
            Rest.setUrl(url);
            Rest.destroy()
                .success(function() {
                    if (parseInt($state.params.project_id) === id) {
                        $state.go("^", null, { reload: true });
                    } else {
                        // @issue: OLD SEARCH
                        // $scope.search(list.iterator);
                    }
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'),
                        msg: i18n.format(i18n._('Call to %s failed. DELETE returned status: '), url) + status });
                });
        };

        Prompt({
            hdr: i18n._('Delete'),
            body: i18n._('<div class="Prompt-bodyQuery">Are you sure you want to delete the project below?</div>') + '<div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>',
            action: action,
            actionText: 'DELETE'
        });
    };

    if ($scope.removeCancelUpdate) {
        $scope.removeCancelUpdate();
    }
    $scope.removeCancelUpdate = $scope.$on('Cancel_Update', function(e, url) {
        // Cancel the project update process
        Rest.setUrl(url);
        Rest.post()
            .success(function () {
                Alert(i18n._('SCM Update Cancel'), i18n._('Your request to cancel the update was submitted to the task manager.'), 'alert-info');
                $scope.refresh();
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'), msg: i18n.format(i18n._('Call to %s failed. POST status: '), url) + status });
            });
    });

    if ($scope.removeCheckCancel) {
        $scope.removeCheckCancel();
    }
    $scope.removeCheckCancel = $scope.$on('Check_Cancel', function(e, data) {
        // Check that we 'can' cancel the update
        var url = data.related.cancel;
        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                if (data.can_cancel) {
                    $scope.$emit('Cancel_Update', url);
                } else {
                    Alert(i18n._('Cancel Not Allowed'), i18n._('<div>Either you do not have access or the SCM update process completed. ' +
                        'Click the <em>Refresh</em> button to view the latest status.</div>'), 'alert-info', null, null, null, null, true);
                }
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'), msg: i18n.format(i18n._('Call to %s failed. GET status: '), url) + status });
            });
    });

    $scope.cancelUpdate = function(id, name) {
        Rest.setUrl(GetBasePath("projects") + id);
        Rest.get()
            .success(function(data) {
                if (data.related.current_update) {
                    Rest.setUrl(data.related.current_update);
                    Rest.get()
                        .success(function(data) {
                            $scope.$emit('Check_Cancel', data);
                        })
                        .error(function (data, status) {
                            ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'),
                                msg: i18n.format(i18n._('Call to %s failed. GET status: '), data.related.current_update) + status });
                        });
                } else {
                    Alert(i18n._('Update Not Found'), i18n.format(i18n._('<div>An SCM update does not appear to be running for project: %s. Click the <em>Refresh</em> ' +
                        'button to view the latest status.</div>'), $filter('sanitize')(name)), 'alert-info',undefined,undefined,undefined,undefined,true);
                }
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'),
                    msg: i18n._('Call to get project failed. GET status: ') + status });
            });
    };

    $scope.SCMUpdate = function(project_id, event) {
        try {
            $(event.target).tooltip('hide');
        } catch (e) {
            // ignore
        }
        $scope.projects.every(function(project) {
            if (project.id === project_id) {
                if (project.scm_type === "Manual" || Empty(project.scm_type)) {
                    // Do not respond. Button appears greyed out as if it is disabled. Not disabled though, because we need mouse over event
                    // to work. So user can click, but we just won't do anything.
                    //Alert('Missing SCM Setup', 'Before running an SCM update, edit the project and provide the SCM access information.', 'alert-info');
                } else if (project.status === 'updating' || project.status === 'running' || project.status === 'pending') {
                    // Alert('Update in Progress', 'The SCM update process is running. Use the Refresh button to monitor the status.', 'alert-info');
                } else {
                    ProjectUpdate({ scope: $scope, project_id: project.id });
                }
                return false;
            }
            return true;
        });
    };

    $scope.editSchedules = function(id) {
        var project = Find({ list: $scope.projects, key: 'id', val: id });
        if (!(project.scm_type === "Manual" || Empty(project.scm_type)) && !(project.status === 'updating' || project.status === 'running' || project.status === 'pending')) {
            $state.go('projectSchedules', { id: id });
        }
    };
}

ProjectsList.$inject = ['$scope', '$rootScope', '$location', '$log', '$stateParams',
    'Rest', 'Alert', 'ProjectList', 'Prompt', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
    'GetBasePath', 'ProjectUpdate', 'Wait', 'GetChoices', 'Empty', 'Find', 'GetProjectIcon',
    'GetProjectToolTip', '$filter', '$state', 'rbacUiControlService', 'Dataset', 'i18n'
];

export function ProjectsAdd($scope, $rootScope, $compile, $location, $log,
    $stateParams, GenerateForm, ProjectsForm, Rest, Alert, ProcessErrors,
    GetBasePath, GetProjectPath, GetChoices, Wait, $state, CreateSelect2, i18n) {

    var form = ProjectsForm(),
        base = $location.path().replace(/^\//, '').split('/')[0],
        defaultUrl = GetBasePath('projects'),
        master = {};

    init();

    function init() {
        Rest.setUrl(GetBasePath('projects'));
        Rest.options()
            .success(function(data) {
                if (!data.actions.POST) {
                    $state.go("^");
                    Alert('Permission Error', 'You do not have permission to add a project.', 'alert-info');
                }
        });

        // apply form definition's default field values
        GenerateForm.applyDefaults(form, $scope);
    }

    GetProjectPath({ scope: $scope, master: master });

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
        var i;
        for (i = 0; i < $scope.scm_type_options.length; i++) {
            if ($scope.scm_type_options[i].value === '') {
                $scope.scm_type_options[i].value = "manual";
                //$scope.scm_type = $scope.scm_type_options[i];
                break;
            }
        }

        CreateSelect2({
            element: '#project_scm_type',
            multiple: false
        });

        $scope.scmRequired = false;
        master.scm_type = $scope.scm_type;
    });

    // Load the list of options for Kind
    GetChoices({
        scope: $scope,
        url: defaultUrl,
        field: 'scm_type',
        variable: 'scm_type_options',
        callback: 'choicesReady'
    });
    CreateSelect2({
        element: '#local-path-select',
        multiple: false
    });

    // Save
    $scope.formSave = function() {
        var i, fld, url, data = {};
        data = {};
        for (fld in form.fields) {
            if (form.fields[fld].type === 'checkbox_group') {
                for (i = 0; i < form.fields[fld].fields.length; i++) {
                    data[form.fields[fld].fields[i].name] = $scope[form.fields[fld].fields[i].name];
                }
            } else {
                if (form.fields[fld].type !== 'alertblock') {
                    data[fld] = $scope[fld];
                }
            }
        }

        if ($scope.scm_type.value === "manual") {
            data.scm_type = "";
            data.local_path = $scope.local_path.value;
        } else {
            data.scm_type = $scope.scm_type.value;
            delete data.local_path;
        }

        url = (base === 'teams') ? GetBasePath('teams') + $stateParams.team_id + '/projects/' : defaultUrl;
        Wait('start');
        Rest.setUrl(url);
        Rest.post(data)
            .success(function(data) {
                $scope.addedItem = data.id;
                $state.go('projects.edit', { id: data.id }, { reload: true });
            })
            .error(function(data, status) {
                Wait('stop');
                ProcessErrors($scope, data, status, form, { hdr: i18n._('Error!'),
                    msg: i18n._('Failed to create new project. POST returned status: ') + status });
            });
    };

    $scope.scmChange = function() {
        // When an scm_type is set, path is not required
        if ($scope.scm_type) {
            $scope.pathRequired = ($scope.scm_type.value === 'manual') ? true : false;
            $scope.scmRequired = ($scope.scm_type.value !== 'manual') ? true : false;
            $scope.scmBranchLabel = ($scope.scm_type.value === 'svn') ? 'Revision #' : 'SCM Branch';
        }

        // Dynamically update popover values
        if ($scope.scm_type.value) {
            switch ($scope.scm_type.value) {
                case 'git':
                    $scope.urlPopover = i18n._('<p>Example URLs for GIT SCM include:</p><ul class=\"no-bullets\"><li>https://github.com/ansible/ansible.git</li>' +
                        '<li>git@github.com:ansible/ansible.git</li><li>git://servername.example.com/ansible.git</li></ul>' +
                        '<p><strong>Note:</strong> When using SSH protocol for GitHub or Bitbucket, enter an SSH key only, ' +
                        'do not enter a username (other than git). Additionally, GitHub and Bitbucket do not support password authentication when using ' +
                        'SSH. GIT read only protocol (git://) does not use username or password information.');
                    break;
                case 'svn':
                    $scope.urlPopover = i18n._('<p>Example URLs for Subversion SCM include:</p>' +
                        '<ul class=\"no-bullets\"><li>https://github.com/ansible/ansible</li><li>svn://servername.example.com/path</li>' +
                        '<li>svn+ssh://servername.example.com/path</li></ul>');
                    break;
                case 'hg':
                    $scope.urlPopover = i18n._('<p>Example URLs for Mercurial SCM include:</p>' +
                        '<ul class=\"no-bullets\"><li>https://bitbucket.org/username/project</li><li>ssh://hg@bitbucket.org/username/project</li>' +
                        '<li>ssh://server.example.com/path</li></ul>' +
                        '<p><strong>Note:</strong> Mercurial does not support password authentication for SSH. ' +
                        'Do not put the username and key in the URL. ' +
                        'If using Bitbucket and SSH, do not supply your Bitbucket username.');
                    break;
                default:
                    $scope.urlPopover = i18n._('<p> URL popover text');
            }
        }

    };
    $scope.formCancel = function() {
        $state.go('projects');
    };
}

ProjectsAdd.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log',
    '$stateParams', 'GenerateForm', 'ProjectsForm', 'Rest', 'Alert', 'ProcessErrors', 'GetBasePath',
    'GetProjectPath', 'GetChoices', 'Wait', '$state', 'CreateSelect2', 'i18n'];


export function ProjectsEdit($scope, $rootScope, $compile, $location, $log,
    $stateParams, ProjectsForm, Rest, Alert, ProcessErrors,
    Prompt, ClearScope, GetBasePath, GetProjectPath, Authorization,
    GetChoices, Empty, DebugForm, Wait, ProjectUpdate, $state, CreateSelect2, ToggleNotification, i18n) {

    ClearScope('htmlTemplate');

    var form = ProjectsForm(),
        defaultUrl = GetBasePath('projects') + $stateParams.project_id + '/',
        master = {},
        id = $stateParams.project_id;

    init();

    function init() {
        $scope.project_local_paths = [];
        $scope.base_dir = '';
    }

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
        var opts = [];

        if (Authorization.getUserInfo('is_superuser') === true) {
            GetProjectPath({ scope: $scope, master: master });
        } else {
            opts.push({
                label: $scope.local_path,
                value: $scope.local_path
            });
            $scope.project_local_paths = opts;
            $scope.local_path = $scope.project_local_paths[0];
            $scope.base_dir = 'You do not have access to view this property';
            $scope.$emit('pathsReady');
        }

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
            .success(function(data) {
                var fld, i;
                for (fld in form.fields) {
                    if (form.fields[fld].type === 'checkbox_group') {
                        for (i = 0; i < form.fields[fld].fields.length; i++) {
                            $scope[form.fields[fld].fields[i].name] = data[form.fields[fld].fields[i].name];
                            master[form.fields[fld].fields[i].name] = data[form.fields[fld].fields[i].name];
                        }
                    } else {
                        if (data[fld] !== undefined) {
                            $scope[fld] = data[fld];
                            master[fld] = data[fld];
                        }
                    }
                    if (form.fields[fld].sourceModel && data.summary_fields &&
                        data.summary_fields[form.fields[fld].sourceModel]) {
                        $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                            data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                        master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
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

                master.scm_type = $scope.scm_type;
                CreateSelect2({
                    element: '#project_scm_type',
                    multiple: false
                });

                $scope.scmBranchLabel = ($scope.scm_type.value === 'svn') ? 'Revision #' : 'SCM Branch';
                $scope.scm_update_tooltip = "Start an SCM update";
                $scope.scm_type_class = "";
                if (data.status === 'running' || data.status === 'updating') {
                    $scope.scm_update_tooltip = "SCM update currently running";
                    $scope.scm_type_class = "btn-disabled";
                }
                if (Empty(data.scm_type)) {
                    $scope.scm_update_tooltip = 'Manual projects do not require an SCM update';
                    $scope.scm_type_class = "btn-disabled";
                }

                $scope.project_obj = data;
                $scope.name = data.name;
                $scope.$emit('projectLoaded');
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, form, { hdr: i18n._('Error!'),
                    msg: i18n._('Failed to retrieve project: ') + id + i18n._('. GET status: ') + status
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
        //generator.clearApiErrors();
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
            .success(function() {
                Wait('stop');
                $state.go($state.current, {}, { reload: true });
            })
            .error(function(data, status) {
                ProcessErrors($scope, data, status, form, { hdr: 'Error!', msg: 'Failed to update project: ' + id + '. PUT status: ' + status });
            });
    };

    // Related set: Delete button
    $scope['delete'] = function(set, itm_id, name, title) {
        var action = function() {
            var url = GetBasePath('projects') + id + '/' + set + '/';
            $rootScope.flashMessage = null;
            Rest.setUrl(url);
            Rest.post({ id: itm_id, disassociate: 1 })
                .success(function() {
                    $('#prompt-modal').modal('hide');
                    // @issue: OLD SEARCH
                    // $scope.search(form.related[set].iterator);
                })
                .error(function(data, status) {
                    $('#prompt-modal').modal('hide');
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url + ' failed. POST returned status: ' + status });
                });
        };

        Prompt({
            hdr: i18n._('Delete'),
            body: i18n.format(i18n._('<div class="Prompt-bodyQuery">Are you sure you want to remove the %s below from %s?</div>'), title, $scope.name) + '<div class="Prompt-bodyTarget">' + name + '</div>',
            action: action,
            actionText: 'DELETE'
        });
    };

    $scope.scmChange = function() {
        if ($scope.scm_type) {
            $scope.pathRequired = ($scope.scm_type.value === 'manual') ? true : false;
            $scope.scmRequired = ($scope.scm_type.value !== 'manual') ? true : false;
            $scope.scmBranchLabel = ($scope.scm_type.value === 'svn') ? 'Revision #' : 'SCM Branch';
        }

        // Dynamically update popover values
        if ($scope.scm_type.value) {
            switch ($scope.scm_type.value) {
                case 'git':
                    $scope.urlPopover = i18n._('<p>Example URLs for GIT SCM include:</p><ul class=\"no-bullets\"><li>https://github.com/ansible/ansible.git</li>' +
                        '<li>git@github.com:ansible/ansible.git</li><li>git://servername.example.com/ansible.git</li></ul>' +
                        '<p><strong>Note:</strong> When using SSH protocol for GitHub or Bitbucket, enter an SSH key only, ' +
                        'do not enter a username (other than git). Additionally, GitHub and Bitbucket do not support password authentication when using ' +
                        'SSH. GIT read only protocol (git://) does not use username or password information.');
                    break;
                case 'svn':
                    $scope.urlPopover = i18n._('<p>Example URLs for Subversion SCM include:</p>' +
                        '<ul class=\"no-bullets\"><li>https://github.com/ansible/ansible</li><li>svn://servername.example.com/path</li>' +
                        '<li>svn+ssh://servername.example.com/path</li></ul>');
                    break;
                case 'hg':
                    $scope.urlPopover = i18n._('<p>Example URLs for Mercurial SCM include:</p>' +
                        '<ul class=\"no-bullets\"><li>https://bitbucket.org/username/project</li><li>ssh://hg@bitbucket.org/username/project</li>' +
                        '<li>ssh://server.example.com/path</li></ul>' +
                        '<p><strong>Note:</strong> Mercurial does not support password authentication for SSH. ' +
                        'Do not put the username and key in the URL. ' +
                        'If using Bitbucket and SSH, do not supply your Bitbucket username.');
                    break;
                default:
                    $scope.urlPopover = i18n._('<p> URL popover text');
            }
        }
    };

    $scope.SCMUpdate = function() {
        if ($scope.project_obj.scm_type === "Manual" || Empty($scope.project_obj.scm_type)) {
            // ignore
        } else if ($scope.project_obj.status === 'updating' || $scope.project_obj.status === 'running' || $scope.project_obj.status === 'pending') {
            Alert('Update in Progress', i18n._('The SCM update process is running.'), 'alert-info');
        } else {
            ProjectUpdate({ scope: $scope, project_id: $scope.project_obj.id });
        }
    };

    $scope.formCancel = function() {
        $state.transitionTo('projects');
    };
}

ProjectsEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log',
    '$stateParams', 'ProjectsForm', 'Rest', 'Alert', 'ProcessErrors', 'Prompt',
    'ClearScope', 'GetBasePath', 'GetProjectPath', 'Authorization', 'GetChoices', 'Empty',
    'DebugForm', 'Wait', 'ProjectUpdate', '$state', 'CreateSelect2', 'ToggleNotification', 'i18n'];
