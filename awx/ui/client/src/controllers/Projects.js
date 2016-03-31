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


export function ProjectsList ($scope, $rootScope, $location, $log, $stateParams,
    Rest, Alert, ProjectList, GenerateList, Prompt, SearchInit,
    PaginateInit, ReturnToCaller, ClearScope, ProcessErrors, GetBasePath,
    SelectionInit, ProjectUpdate, Refresh, Wait, GetChoices, Empty,
    Find, GetProjectIcon, GetProjectToolTip, $filter, $state) {

    ClearScope();

    Wait('start');

    var list = ProjectList,
        defaultUrl = GetBasePath('projects'),
        view = GenerateList,
        base = $location.path().replace(/^\//, '').split('/')[0],
        mode = (base === 'projects') ? 'edit' : 'select',
        url = (base === 'teams') ? GetBasePath('teams') + $stateParams.team_id + '/projects/' : defaultUrl,
        choiceCount = 0;

    view.inject(list, { mode: mode, scope: $scope });

    $rootScope.flashMessage = null;
    $scope.projectLoading = true;

    if (mode === 'select') {
        SelectionInit({
            scope: $scope,
            list: list,
            url: url,
            returnToCaller: 1
        });
    }

    if ($scope.removePostRefresh) {
        $scope.removePostRefresh();
    }
    $scope.removePostRefresh = $scope.$on('PostRefresh', function () {
        Wait('stop');
        if ($scope.projects) {
            $scope.projects.forEach(function(project, i) {
                $scope.projects[i].statusIcon = GetProjectIcon(project.status);
                $scope.projects[i].statusTip = GetProjectToolTip(project.status);
                $scope.projects[i].scm_update_tooltip = "Start an SCM update";
                $scope.projects[i].scm_schedule_tooltip = "Schedule future SCM updates";
                $scope.projects[i].scm_type_class = "";

                if (project.status === 'failed' && project.summary_fields.last_update && project.summary_fields.last_update.status === 'canceled') {
                    $scope.projects[i].statusTip = 'Canceled. Click for details';
                }

                if (project.status === 'running' || project.status === 'updating') {
                    $scope.projects[i].scm_update_tooltip = "SCM update currently running";
                    $scope.projects[i].scm_type_class = "btn-disabled";
                }

                $scope.project_scm_type_options.forEach(function(type) {
                    if (type.value === project.scm_type) {
                        $scope.projects[i].scm_type = type.label;
                        if (type.label === 'Manual') {
                            $scope.projects[i].scm_update_tooltip = 'Manual projects do not require an SCM update';
                            $scope.projects[i].scm_schedule_tooltip = 'Manual projects do not require a schedule';
                            $scope.projects[i].scm_type_class = 'btn-disabled';
                            $scope.projects[i].statusTip = 'Not configured for SCM';
                            $scope.projects[i].statusIcon = 'none';
                        }
                    }
                });
            });
        }
    });

    // Handle project update status changes
    if ($rootScope.removeJobStatusChange) {
        $rootScope.removeJobStatusChange();
    }
    $rootScope.removeJobStatusChange = $rootScope.$on('JobStatusChange-projects', function(e, data) {
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
                    $scope.search(list.iterator, null, null, null, null, false);
                }
                else {
                    project.scm_update_tooltip = "SCM update currently running";
                    project.scm_type_class = "btn-disabled";
                }
                project.status = data.status;
                project.statusIcon = GetProjectIcon(data.status);
                project.statusTip = GetProjectToolTip(data.status);
            }
        }
    });

    if ($scope.removeChoicesHere) {
        $scope.removeChoicesHere();
    }
    $scope.removeChoicesHere = $scope.$on('choicesCompleteProjectList', function () {
        var opt;

        list.fields.scm_type.searchOptions = $scope.project_scm_type_options;
        list.fields.status.searchOptions = $scope.project_status_options;

        if ($stateParams.scm_type && $stateParams.status) {
            // Request coming from home page. User wants all errors for an scm_type
            defaultUrl += '?status=' + $stateParams.status;
        }

        SearchInit({
            scope: $scope,
            set: 'projects',
            list: list,
            url: defaultUrl
        });
        PaginateInit({
            scope: $scope,
            list: list,
            url: defaultUrl
        });

        if ($stateParams.scm_type) {
            $scope[list.iterator + 'SearchType'] = '';
            $scope[list.iterator + 'SearchField'] = 'scm_type';
            $scope[list.iterator + 'SelectShow'] = true;
            $scope[list.iterator + 'SearchSelectOpts'] = list.fields.scm_type.searchOptions;
            $scope[list.iterator + 'SearchFieldLabel'] = list.fields.scm_type.label.replace(/<br\>/g, ' ');
            for (opt in list.fields.scm_type.searchOptions) {
                if (list.fields.scm_type.searchOptions[opt].value === $stateParams.scm_type) {
                    $scope[list.iterator + 'SearchSelectValue'] = list.fields.scm_type.searchOptions[opt];
                    break;
                }
            }
        } else if ($stateParams.status) {
            $scope[list.iterator + 'SearchType'] = '';
            $scope[list.iterator + 'SearchValue'] = $stateParams.status;
            $scope[list.iterator + 'SearchField'] = 'status';
            $scope[list.iterator + 'SelectShow'] = true;
            $scope[list.iterator + 'SearchFieldLabel'] = list.fields.status.label;
            $scope[list.iterator + 'SearchSelectOpts'] = list.fields.status.searchOptions;
            for (opt in list.fields.status.searchOptions) {
                if (list.fields.status.searchOptions[opt].value === $stateParams.status) {
                    $scope[list.iterator + 'SearchSelectValue'] = list.fields.status.searchOptions[opt];
                    break;
                }
            }
        }
        $scope.search(list.iterator);
    });

    if ($scope.removeChoicesReadyList) {
        $scope.removeChoicesReadyList();
    }
    $scope.removeChoicesReadyList = $scope.$on('choicesReadyProjectList', function () {
        choiceCount++;
        if (choiceCount === 2) {
            $scope.$emit('choicesCompleteProjectList');
        }
    });

    // Load options for status --used in search
    GetChoices({
        scope: $scope,
        url: defaultUrl,
        field: 'status',
        variable: 'project_status_options',
        callback: 'choicesReadyProjectList'
    });

    // Load the list of options for Kind
    GetChoices({
        scope: $scope,
        url: defaultUrl,
        field: 'scm_type',
        variable: 'project_scm_type_options',
        callback: 'choicesReadyProjectList'
    });

    $scope.addProject = function () {
        $state.transitionTo('projects.add');
    };

    $scope.editProject = function (id) {
        $state.transitionTo('projects.edit', {id: id});
    };

    if ($scope.removeGoToJobDetails) {
        $scope.removeGoToJobDetails();
    }
    $scope.removeGoToJobDetails = $scope.$on('GoToJobDetails', function(e, data) {
        if (data.summary_fields.current_update || data.summary_fields.last_update) {

            Wait('start');

            // Grab the id from summary_fields
            var id = (data.summary_fields.current_update) ? data.summary_fields.current_update.id : data.summary_fields.last_update.id;

            $state.go('scmUpdateStdout', {id: id});

        } else {
            Alert('No Updates Available', 'There is no SCM update information available for this project. An update has not yet been ' +
                ' completed.  If you have not already done so, start an update for this project.', 'alert-info');
        }
    });

    $scope.showSCMStatus = function (id) {
        // Refresh the project list
        var project = Find({ list: $scope.projects, key: 'id', val: id });
        if (Empty(project.scm_type) || project.scm_type === 'Manual') {
            Alert('No SCM Configuration', 'The selected project is not configured for SCM. To configure for SCM, edit the project and provide SCM settings, ' +
                'and then run an update.', 'alert-info');
        } else {
            // Refresh what we have in memory to insure we're accessing the most recent status record
            Rest.setUrl(project.url);
            Rest.get()
                .success(function(data) {
                    $scope.$emit('GoToJobDetails', data);
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Project lookup failed. GET returned: ' + status });
                });
        }
    };

    $scope.deleteProject = function (id, name) {
        var action = function () {
            $('#prompt-modal').modal('hide');
            Wait('start');
            var url = defaultUrl + id + '/';
            Rest.setUrl(url);
            Rest.destroy()
                .success(function () {
                    $scope.search(list.iterator);
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the project below?</div><div class="Prompt-bodyTarget">' + name + '</div>',
            action: action,
            actionText: 'DELETE'
        });
    };

    if ($scope.removeCancelUpdate) {
        $scope.removeCancelUpdate();
    }
    $scope.removeCancelUpdate = $scope.$on('Cancel_Update', function (e, url) {
        // Cancel the project update process
        Rest.setUrl(url);
        Rest.post()
            .success(function () {
                Alert('SCM Update Cancel', 'Your request to cancel the update was submitted to the task manager.', 'alert-info');
                $scope.refresh();
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url + ' failed. POST status: ' + status });
            });
    });

    if ($scope.removeCheckCancel) {
        $scope.removeCheckCancel();
    }
    $scope.removeCheckCancel = $scope.$on('Check_Cancel', function (e, data) {
        // Check that we 'can' cancel the update
        var url = data.related.cancel;
        Rest.setUrl(url);
        Rest.get()
            .success(function (data) {
                if (data.can_cancel) {
                    $scope.$emit('Cancel_Update', url);
                } else {
                    Alert('Cancel Not Allowed', 'Either you do not have access or the SCM update process completed. ' +
                        'Click the <em>Refresh</em> button to view the latest status.', 'alert-info', null, null, null, null, true);
                }
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url + ' failed. GET status: ' + status });
            });
    });

    $scope.cancelUpdate = function (id, name) {
        Rest.setUrl(GetBasePath("projects") + id);
        Rest.get()
            .success(function (data) {
                if (data.related.current_update) {
                    Rest.setUrl(data.related.current_update);
                    Rest.get()
                        .success(function (data) {
                            $scope.$emit('Check_Cancel', data);
                        })
                        .error(function (data, status) {
                            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call to ' + data.related.current_update + ' failed. GET status: ' + status });
                        });
                } else {
                    Alert('Update Not Found', 'An SCM update does not appear to be running for project: ' + $filter('sanitize')(name) + '. Click the <em>Refresh</em> ' +
                        'button to view the latest status.', 'alert-info',undefined,undefined,undefined,undefined,true);
                }
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to get project failed. GET status: ' + status });
            });
    };

    $scope.refresh = function () {
        $scope.search(list.iterator);
    };

    $scope.SCMUpdate = function (project_id, event) {
        try {
            $(event.target).tooltip('hide');
        }
        catch(e) {
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
        if (project.scm_type === "Manual" || Empty(project.scm_type)) {
            // Nothing to do
        }
        else {
            $location.path('/projects/' + id + '/schedules');
        }
    };
}

ProjectsList.$inject = ['$scope', '$rootScope', '$location', '$log',
    '$stateParams', 'Rest', 'Alert', 'ProjectList', 'generateList', 'Prompt',
    'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
    'ProcessErrors', 'GetBasePath', 'SelectionInit', 'ProjectUpdate',
    'Refresh', 'Wait', 'GetChoices', 'Empty', 'Find',
    'GetProjectIcon', 'GetProjectToolTip', '$filter', '$state'
];


export function ProjectsAdd(Refresh, $scope, $rootScope, $compile, $location, $log,
    $stateParams, ProjectsForm, GenerateForm, Rest, Alert, ProcessErrors,
    ClearScope, GetBasePath, ReturnToCaller, GetProjectPath, LookUpInit,
    OrganizationList, CredentialList, GetChoices, DebugForm, Wait, $state,
    CreateSelect2) {

    ClearScope();

    // Inject dynamic view
    var form = ProjectsForm(),
        generator = GenerateForm,
        base = $location.path().replace(/^\//, '').split('/')[0],
        defaultUrl = GetBasePath('projects'),
        master = {};

    generator.inject(form, { mode: 'add', related: false, scope: $scope });
    generator.reset();

    GetProjectPath({ scope: $scope, master: master });

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReady', function () {
        var i;
        for (i = 0; i < $scope.scm_type_options.length; i++) {
            if ($scope.scm_type_options[i].value === '') {
                $scope.scm_type_options[i].value="manual";
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

    LookUpInit({
        scope: $scope,
        form: form,
        list: OrganizationList,
        field: 'organization',
        input_type: 'radio'
    });

    LookUpInit({
        scope: $scope,
        url: GetBasePath('credentials') + '?kind=scm',
        form: form,
        list: CredentialList,
        field: 'credential',
        input_type: "radio"
    });

    // Save
    $scope.formSave = function () {
        var i, fld, url, data={};
        generator.clearApiErrors();
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

        if($scope.scm_type.value === "manual"){
            data.scm_type = "" ;
            data.local_path = $scope.local_path.value;
        } else {
            data.scm_type = $scope.scm_type.value;
            delete data.local_path;
        }

        url = (base === 'teams') ? GetBasePath('teams') + $stateParams.team_id + '/projects/' : defaultUrl;
        Wait('start');
        Rest.setUrl(url);
        Rest.post(data)
            .success(function (data) {
                $scope.addedItem = data.id;

                Refresh({
                    scope: $scope,
                    set: 'projects',
                    iterator: 'project',
                    url: $scope.current_url
                });

                $state.go("^");
            })
            .error(function (data, status) {
                Wait('stop');
                ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                    msg: 'Failed to create new project. POST returned status: ' + status });
            });
    };

    $scope.scmChange = function () {
        // When an scm_type is set, path is not required
        if ($scope.scm_type) {
            $scope.pathRequired = ($scope.scm_type.value === 'manual') ? true : false;
            $scope.scmRequired = ($scope.scm_type.value !== 'manual') ? true : false;
            $scope.scmBranchLabel = ($scope.scm_type.value === 'svn') ? 'Revision #' : 'SCM Branch';
        }
    };

    $scope.formCancel = function () {
        $state.transitionTo('projects');
    };
}

ProjectsAdd.$inject = ['Refresh', '$scope', '$rootScope', '$compile', '$location', '$log',
    '$stateParams', 'ProjectsForm', 'GenerateForm', 'Rest', 'Alert',
    'ProcessErrors', 'ClearScope', 'GetBasePath', 'ReturnToCaller',
    'GetProjectPath', 'LookUpInit', 'OrganizationList', 'CredentialList',
    'GetChoices', 'DebugForm', 'Wait', '$state', 'CreateSelect2'
];


export function ProjectsEdit($scope, $rootScope, $compile, $location, $log,
    $stateParams, ProjectsForm, GenerateForm, Rest, Alert, ProcessErrors,
    RelatedSearchInit, RelatedPaginateInit, Prompt, ClearScope, GetBasePath,
    ReturnToCaller, GetProjectPath, Authorization, CredentialList, LookUpInit,
    GetChoices, Empty, DebugForm, Wait, SchedulesControllerInit,
    SchedulesListInit, SchedulesList, ProjectUpdate, $state, CreateSelect2) {

    ClearScope('htmlTemplate');

    // Inject dynamic view
    var form = ProjectsForm(),
        generator = GenerateForm,
        defaultUrl = GetBasePath('projects') + $stateParams.id + '/',
        base = $location.path().replace(/^\//, '').split('/')[0],
        master = {}, i,
        id = $stateParams.id,
        relatedSets = {};

    SchedulesList.well = false;
    generator.inject(form, {
        mode: 'edit',
        related: true,
        scope: $scope
    });
    generator.reset();

    $scope.project_local_paths = [];
    $scope.base_dir = '';

    if ($scope.removerelatedschedules) {
        $scope.removerelatedschedules();
    }
    $scope.removerelatedschedules = $scope.$on('relatedschedules', function() {
        SchedulesListInit({
            scope: $scope,
            list: SchedulesList,
            choices: null,
            related: true
        });
    });

    // After the project is loaded, retrieve each related set
    if ($scope.projectLoadedRemove) {
        $scope.projectLoadedRemove();
    }
    $scope.projectLoadedRemove = $scope.$on('projectLoaded', function () {
        var set, opts=[];

        for (set in relatedSets) {
            $scope.search(relatedSets[set].iterator);
        }

        SchedulesControllerInit({
            scope: $scope,
            parent_scope: $scope,
            iterator: 'schedule'
        });

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
        }

        LookUpInit({
            url: GetBasePath('credentials') + '?kind=scm',
            scope: $scope,
            form: form,
            list: CredentialList,
            field: 'credential',
            input_type: 'radio'
        });

        $scope.pathRequired = ($scope.scm_type.value === 'manual') ? true : false;
        $scope.scmRequired = ($scope.scm_type.value !== 'manual') ? true : false;
        $scope.scmBranchLabel = ($scope.scm_type.value === 'svn') ? 'Revision #' : 'SCM Branch';
        Wait('stop');
    });

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReady', function () {
        for (i = 0; i < $scope.scm_type_options.length; i++) {
            if ($scope.scm_type_options[i].value === '') {
                $scope.scm_type_options[i].value = "manual";
                break;
            }
        }
        // Retrieve detail record and prepopulate the form
        Rest.setUrl(defaultUrl);
        Rest.get({ params: { id: id } })
            .success(function (data) {
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
                    if (fld !== 'organization' && form.fields[fld].sourceModel &&
                        data.summary_fields && data.summary_fields[form.fields[fld].sourceModel]) {
                        $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                            data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                        master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                            data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                    }
                }
                relatedSets = form.relatedSets(data.related);



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

                // Initialize related search functions. Doing it here to make sure relatedSets object is populated.
                RelatedSearchInit({
                    scope: $scope,
                    form: form,
                    relatedSets: relatedSets
                });
                RelatedPaginateInit({
                    scope: $scope,
                    relatedSets: relatedSets
                });

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
                $scope.$emit('projectLoaded');
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                    msg: 'Failed to retrieve project: ' + id + '. GET status: ' + status
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

    // Save changes to the parent
    $scope.formSave = function () {
        var fld, i, params;
        generator.clearApiErrors();
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

        if($scope.scm_type.value === "manual"){
            params.scm_type = "" ;
            params.local_path = $scope.local_path.value;
        } else {
            params.scm_type = $scope.scm_type.value;
            delete params.local_path;
        }

        Rest.setUrl(defaultUrl);
        Rest.put(params)
            .success(function() {
                Wait('stop');
                /*$scope.scm_update_tooltip = "Start an SCM update";
                $scope.scm_type_class = "";
                if (Empty($scope.scm_type)) {
                    $scope.scm_update_tooltip = 'Manual projects do not require an SCM update';
                    $scope.scm_type_class = "btn-disabled";
                }*/
                ReturnToCaller();
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, form, { hdr: 'Error!', msg: 'Failed to update project: ' + id + '. PUT status: ' + status });
            });
    };

    // Related set: Add button
    $scope.add = function (set) {
        $rootScope.flashMessage = null;
        $location.path('/' + base + '/' + $stateParams.id + '/' + set);
    };

    // Related set: Edit button
    $scope.edit = function (set, id) {
        $rootScope.flashMessage = null;
        $location.path('/' + set + '/' + id);
    };

    // Related set: Delete button
    $scope['delete'] = function (set, itm_id, name, title) {
        var action = function () {
            var url = GetBasePath('projects') + id + '/' + set + '/';
            $rootScope.flashMessage = null;
            Rest.setUrl(url);
            Rest.post({ id: itm_id, disassociate: 1 })
                .success(function () {
                    $('#prompt-modal').modal('hide');
                    $scope.search(form.related[set].iterator);
                })
                .error(function (data, status) {
                    $('#prompt-modal').modal('hide');
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url + ' failed. POST returned status: ' + status });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: '<div class="Prompt-bodyQuery">Are you sure you want to remove the ' + title + ' below from ' + $scope.name + '?</div><div class="Prompt-bodyTarget">' + name + '</div>',
            action: action,
            actionText: 'DELETE'
        });
    };

    $scope.scmChange = function () {
        if ($scope.scm_type) {
            $scope.pathRequired = ($scope.scm_type.value === 'manual') ? true : false;
            $scope.scmRequired = ($scope.scm_type.value !== 'manual') ? true : false;
            $scope.scmBranchLabel = ($scope.scm_type.value === 'svn') ? 'Revision #' : 'SCM Branch';
        }
    };

    $scope.SCMUpdate = function () {
        if ($scope.project_obj.scm_type === "Manual" || Empty($scope.project_obj.scm_type)) {
            // ignore
        } else if ($scope.project_obj.status === 'updating' || $scope.project_obj.status === 'running' || $scope.project_obj.status === 'pending') {
            Alert('Update in Progress', 'The SCM update process is running.', 'alert-info');
        } else {
            ProjectUpdate({ scope: $scope, project_id: $scope.project_obj.id });
        }
    };

    $scope.formCancel = function () {
        $state.transitionTo('projects');
    };
}

ProjectsEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log',
    '$stateParams', 'ProjectsForm', 'GenerateForm', 'Rest', 'Alert',
    'ProcessErrors', 'RelatedSearchInit', 'RelatedPaginateInit', 'Prompt',
    'ClearScope', 'GetBasePath', 'ReturnToCaller', 'GetProjectPath',
    'Authorization', 'CredentialList', 'LookUpInit', 'GetChoices', 'Empty',
    'DebugForm', 'Wait', 'SchedulesControllerInit', 'SchedulesListInit',
    'SchedulesList', 'ProjectUpdate', '$state', 'CreateSelect2'
];
