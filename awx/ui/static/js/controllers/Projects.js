/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Projects.js
 *
 *  Controller functions for the Projects model.
 *
 */
/**
 * @ngdoc function
 * @name controllers.function:Projects
 * @description This controller's for the projects page
*/
'use strict';

function ProjectsList ($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, ProjectList, GenerateList, LoadBreadCrumbs,
    Prompt, SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors, GetBasePath, SelectionInit, ProjectUpdate,
    Refresh, Wait, Stream, GetChoices, Empty, Find, LogViewer, GetProjectIcon, GetProjectToolTip) {

    ClearScope();

    Wait('start');

    var list = ProjectList,
        defaultUrl = GetBasePath('projects'),
        view = GenerateList,
        base = $location.path().replace(/^\//, '').split('/')[0],
        mode = (base === 'projects') ? 'edit' : 'select',
        url = (base === 'teams') ? GetBasePath('teams') + $routeParams.team_id + '/projects/' : defaultUrl,
        choiceCount = 0;

    view.inject(list, { mode: mode, scope: $scope, breadCrumbs:(($routeParams.team_id) ? true : false)});

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
    $rootScope.removeJobStatusChange = $rootScope.$on('JobStatusChange', function(e, data) {
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
    $scope.removeChoicesHere = $scope.$on('choicesCompleteProject', function () {
        var opt;

        list.fields.scm_type.searchOptions = $scope.project_scm_type_options;
        list.fields.status.searchOptions = $scope.project_status_options;

        if ($routeParams.scm_type && $routeParams.status) {
            // Request coming from home page. User wants all errors for an scm_type
            defaultUrl += '?status=' + $routeParams.status;
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

        if ($routeParams.scm_type) {
            $scope[list.iterator + 'SearchType'] = '';
            $scope[list.iterator + 'SearchField'] = 'scm_type';
            $scope[list.iterator + 'SelectShow'] = true;
            $scope[list.iterator + 'SearchSelectOpts'] = list.fields.scm_type.searchOptions;
            $scope[list.iterator + 'SearchFieldLabel'] = list.fields.scm_type.label.replace(/<br\>/g, ' ');
            for (opt in list.fields.scm_type.searchOptions) {
                if (list.fields.scm_type.searchOptions[opt].value === $routeParams.scm_type) {
                    $scope[list.iterator + 'SearchSelectValue'] = list.fields.scm_type.searchOptions[opt];
                    break;
                }
            }
        } else if ($routeParams.status) {
            $scope[list.iterator + 'SearchType'] = '';
            $scope[list.iterator + 'SearchValue'] = $routeParams.status;
            $scope[list.iterator + 'SearchField'] = 'status';
            $scope[list.iterator + 'SelectShow'] = true;
            $scope[list.iterator + 'SearchFieldLabel'] = list.fields.status.label;
            $scope[list.iterator + 'SearchSelectOpts'] = list.fields.status.searchOptions;
            for (opt in list.fields.status.searchOptions) {
                if (list.fields.status.searchOptions[opt].value === $routeParams.status) {
                    $scope[list.iterator + 'SearchSelectValue'] = list.fields.status.searchOptions[opt];
                    break;
                }
            }
        }
        $scope.search(list.iterator);
    });

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReadyProject', function () {
        choiceCount++;
        if (choiceCount === 2) {
            $scope.$emit('choicesCompleteProject');
        }
    });

    // Load options for status --used in search
    GetChoices({
        scope: $scope,
        url: defaultUrl,
        field: 'status',
        variable: 'project_status_options',
        callback: 'choicesReadyProject'
    });

    // Load the list of options for Kind
    GetChoices({
        scope: $scope,
        url: defaultUrl,
        field: 'scm_type',
        variable: 'project_scm_type_options',
        callback: 'choicesReadyProject'
    });

    LoadBreadCrumbs();

    $scope.showActivity = function () {
        Stream({ scope: $scope });
    };

    $scope.addProject = function () {
        $location.path($location.path() + '/add');
    };

    $scope.editProject = function (id) {
        $location.path($location.path() + '/' + id);
    };

    if ($scope.removeShowLogViewer) {
        $scope.removeShowLogViewer();
    }
    $scope.removeShowLogViewer = $scope.$on('ShowLogViewer', function(e, data) {
        if (data.related.current_update) {
            Wait('start');
            LogViewer({
                scope: $scope,
                url: data.related.current_update,
                getIcon: GetProjectIcon
            });
        } else if (data.related.last_update) {
            Wait('start');
            LogViewer({
                scope: $scope,
                url: data.related.last_update,
                getIcon: GetProjectIcon
            });
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
                    $scope.$emit('ShowLogViewer', data);
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
            body: 'Are you sure you want to delete ' + name + '?',
            action: action
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
                        'Click the <em>Refresh</em> button to view the latest status.', 'alert-info');
                }
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url + ' failed. GET status: ' + status });
            });
    });

    $scope.cancelUpdate = function (id, name) {
        // Start the cancel process
        var i, project, found = false;
        for (i = 0; i < $scope.projects.length; i++) {
            if ($scope.projects[i].id === id) {
                project = $scope.projects[i];
                found = true;
                break;
            }
        }
        if (found && project.related.current_update) {
            Rest.setUrl(project.related.current_update);
            Rest.get()
                .success(function (data) {
                    $scope.$emit('Check_Cancel', data);
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + project.related.current_update + ' failed. GET status: ' + status });
                });
        } else {
            Alert('Update Not Found', 'An SCM update does not appear to be running for project: ' + name + '. Click the <em>Refresh</em> ' +
                'button to view the latet status.', 'alert-info');
        }
    };

    $scope.refresh = function () {
        /*Wait('start');
        $scope.projectLoading = false;
        Refresh({
            scope: $scope,
            set: 'projects',
            iterator: 'project',
            url: $scope.current_url
        });*/
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

ProjectsList.$inject = ['$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'ProjectList', 'GenerateList',
    'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors', 'GetBasePath',
    'SelectionInit', 'ProjectUpdate', 'Refresh', 'Wait', 'Stream', 'GetChoices', 'Empty', 'Find',
    'LogViewer', 'GetProjectIcon', 'GetProjectToolTip'
];


function ProjectsAdd($scope, $rootScope, $compile, $location, $log, $routeParams, ProjectsForm, GenerateForm, Rest, Alert, ProcessErrors,
    LoadBreadCrumbs, ClearScope, GetBasePath, ReturnToCaller, GetProjectPath, LookUpInit, OrganizationList,
    CredentialList, GetChoices, DebugForm, Wait) {

    ClearScope();

    // Inject dynamic view
    var form = ProjectsForm(),
        generator = GenerateForm,
        base = $location.path().replace(/^\//, '').split('/')[0],
        defaultUrl = GetBasePath('projects'),
        master = {};

    generator.inject(form, { mode: 'add', related: false, scope: $scope });
    generator.reset();
    LoadBreadCrumbs();

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
        if(data.scm_type.value==="manual" ){
            data.scm_type = "";
        } else data.scm_type = $scope.scm_type.value;
        if ($scope.scm_type.value !== '') {
            delete data.local_path;
        } else {
            data.local_path = $scope.local_path.value;
        }

        url = (base === 'teams') ? GetBasePath('teams') + $routeParams.team_id + '/projects/' : defaultUrl;
        Wait('start');
        Rest.setUrl(url);
        Rest.post(data)
            .success(function (data) {
                var id = data.id,
                    url = GetBasePath('projects') + id + '/organizations/',
                    org = { id: $scope.organization };
                Rest.setUrl(url);
                Rest.post(org)
                    .success(function () {
                        Wait('stop');
                        $rootScope.flashMessage = "New project successfully created!";
                        if (base === 'projects') {
                            ReturnToCaller();
                        }
                        else {
                            ReturnToCaller(1);
                        }
                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                            msg: 'Failed to add organization to project. POST returned status: ' + status });
                    });
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

    // Cancel
    $scope.formReset = function () {
        var fld;
        $rootScope.flashMessage = null;
        generator.reset();
        for (fld in master) {
            $scope[fld] = master[fld];
        }
        $scope.scmChange();
    };
}

ProjectsAdd.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'ProjectsForm',
    'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath',
    'ReturnToCaller', 'GetProjectPath', 'LookUpInit', 'OrganizationList', 'CredentialList', 'GetChoices',
    'DebugForm', 'Wait'
];


function ProjectsEdit($scope, $rootScope, $compile, $location, $log, $routeParams, ProjectsForm,
    GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, RelatedPaginateInit, Prompt,
    ClearScope, GetBasePath, ReturnToCaller, GetProjectPath, Authorization, CredentialList, LookUpInit, GetChoices,
    Empty, DebugForm, Wait, Stream, SchedulesControllerInit, SchedulesListInit, SchedulesList, ProjectUpdate) {

    ClearScope('htmlTemplate');

    // Inject dynamic view
    var form = ProjectsForm(),
        generator = GenerateForm,
        defaultUrl = GetBasePath('projects') + $routeParams.id + '/',
        base = $location.path().replace(/^\//, '').split('/')[0],
        master = {},
        id = $routeParams.id,
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

        $scope.pathRequired = ($scope.scm_type.value === '') ? true : false;
        $scope.scmRequired = ($scope.scm_type.value !== '') ? true : false;
        $scope.scmBranchLabel = ($scope.scm_type.value === 'svn') ? 'Revision #' : 'SCM Branch';
        Wait('stop');
    });

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReady', function () {
        // Retrieve detail record and prepopulate the form
        Rest.setUrl(defaultUrl);
        Rest.get({ params: { id: id } })
            .success(function (data) {
                var fld, i;
                LoadBreadCrumbs({ path: '/projects/' + id, title: data.name });
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

                data.scm_type = (Empty(data.scm_type)) ? '' : data.scm_type;

                for (i = 0; i < $scope.scm_type_options.length; i++) {
                    if ($scope.scm_type_options[i].value === data.scm_type) {
                        $scope.scm_type = $scope.scm_type_options[i];
                        break;
                    }
                }

                if ($scope.scm_type.value !== '') {
                    $scope.pathRequired = false;
                    $scope.scmRequired = true;
                } else {
                    $scope.pathRequired = true;
                    $scope.scmRequired = false;
                }

                master.scm_type = $scope.scm_type;
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

    // Handle project update status changes
    if ($rootScope.removeJobStatusChange) {
        $rootScope.removeJobStatusChange();
    }
    $rootScope.removeJobStatusChange = $rootScope.$on('JobStatusChange', function(e, data) {
        if ($scope.project_obj && data.project_id === $scope.project_obj.id) {
            // This is the affected project
            $log.debug('Received event for project: ' + $scope.project_obj.name);
            $log.debug('Status changed to: ' + data.status);
            // Set the status and re-evaluate the update button tooltip and class
            $scope.project_obj.status = data.status;
            $scope.scm_update_tooltip = "Start an SCM update";
            $scope.scm_type_class = "";
            if (data.status === 'running' || data.status === 'updating') {
                $scope.scm_update_tooltip = "SCM update currently running";
                $scope.scm_type_class = "btn-disabled";
            }
            if (Empty($scope.project_obj.scm_type)) {
                $scope.scm_update_tooltip = 'Manual projects do not require an SCM update';
                $scope.scm_type_class = "btn-disabled";
            }
        }
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

        params.scm_type = $scope.scm_type.value;
        if ($scope.scm_type.value !== '') {
            delete params.local_path;
        } else {
            params.local_path = $scope.local_path.value;
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

    $scope.showActivity = function () {
        Stream({ scope: $scope });
    };

    // Related set: Add button
    $scope.add = function (set) {
        $rootScope.flashMessage = null;
        $location.path('/' + base + '/' + $routeParams.id + '/' + set);
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
            body: 'Are you sure you want to remove ' + name + ' from ' + $scope.name + ' ' + title + '?',
            action: action
        });
    };

    $scope.scmChange = function () {
        if ($scope.scm_type) {
            $scope.pathRequired = ($scope.scm_type.value === '') ? true : false;
            $scope.scmRequired = ($scope.scm_type.value !== '') ? true : false;
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

    // Reset the form
    $scope.formReset = function () {
        $rootScope.flashMessage = null;
        generator.reset();
        for (var fld in master) {
            $scope[fld] = master[fld];
        }
        $scope.scmChange();
    };
}

ProjectsEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'ProjectsForm', 'GenerateForm',
    'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 'RelatedPaginateInit', 'Prompt', 'ClearScope',
    'GetBasePath', 'ReturnToCaller', 'GetProjectPath', 'Authorization', 'CredentialList', 'LookUpInit', 'GetChoices', 'Empty',
    'DebugForm', 'Wait', 'Stream', 'SchedulesControllerInit', 'SchedulesListInit', 'SchedulesList', 'ProjectUpdate'
];
