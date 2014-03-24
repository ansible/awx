/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Jobs.js
 *
 *  Controller functions for the Inventory model.
 *
 */
 
'use strict';

function JobsListController ($scope, $compile, ClearScope, Breadcrumbs, LoadBreadCrumbs, LoadScope, RunningJobsList, CompletedJobsList, QueuedJobsList,
    ScheduledJobsList, GetChoices, GetBasePath, Wait, DeleteJob) {
    
    ClearScope();

    var e,
        completed_scope, running_scope, queued_scope, scheduled_scope,
        choicesCount = 0, listsCount = 0;

    LoadBreadCrumbs();

    // Add breadcrumbs
    e = angular.element(document.getElementById('breadcrumbs'));
    e.html(Breadcrumbs({ list: { editTitle: 'Jobs' } , mode: 'edit' }));
    $compile(e)($scope);

    // After all the lists are loaded
    if ($scope.removeListLoaded) {
        $scope.removeListLoaded();
    }
    $scope.removeListLoaded = $scope.$on('listLoaded', function() {
        listsCount++;
        if (listsCount === 3) {
            Wait('stop');
        }
    });
    
    // After all choices are ready, load up the lists and populate the page
    if ($scope.removeBuildJobsList) {
        $scope.removeBuildJobsList();
    }
    $scope.removeBuildJobsList = $scope.$on('buildJobsList', function() {
        completed_scope = $scope.$new();
        LoadScope({
            parent_scope: $scope,
            scope: completed_scope,
            list: CompletedJobsList,
            id: 'completed-jobs',
            url: GetBasePath('unified_jobs') + '?status__in=(succesful,failed,error,canceled)'     ///static/sample/data/jobs/completed/data.json'
        });
        running_scope = $scope.$new();
        LoadScope({
            parent_scope: $scope,
            scope: running_scope,
            list: RunningJobsList,
            id: 'active-jobs',
            url: GetBasePath('unified_jobs') + '?status=running'
        });
        queued_scope = $scope.$new();
        LoadScope({
            parent_scope: $scope,
            scope: queued_scope,
            list: QueuedJobsList,
            id: 'queued-jobs',
            url: GetBasePath('unified_jobs') + '?status__in(pending,waiting,new)'              //'/static/sample/data/jobs/queued/data.json'
        });
        scheduled_scope = $scope.$new();
        LoadScope({
            parent_scope: $scope,
            scope: scheduled_scope,
            list: ScheduledJobsList,
            id: 'scheduled-jobs',
            url: GetBasePath('schedules')
        });

        completed_scope.deleteJob = function(id) {
            DeleteJob({ scope: completed_scope, id: id });
        };

        queued_scope.deleteJob = function(id) {
            DeleteJob({ scope: queued_scope, id: id });
        };

        running_scope.deleteJob = function(id) {
            DeleteJob({ scope: running_scope, id: id });
        };
        
    });

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
        choicesCount++;
        if (choicesCount === 2) {
            $scope.$emit('buildJobsList');
        }
    });

    Wait('start');

    GetChoices({
        scope: $scope,
        url: GetBasePath('jobs'),
        field: 'status',
        variable: 'status_choices',
        callback: 'choicesReady'
    });
    
    GetChoices({
        scope: $scope,
        url: '/static/sample/data/types/data.json',     //GetBasePath('jobs')
        field: 'type',
        variable: 'type_choices',
        callback: 'choicesReady'
    });

}

JobsListController.$inject = ['$scope', '$compile', 'ClearScope', 'Breadcrumbs', 'LoadBreadCrumbs', 'LoadScope', 'RunningJobsList', 'CompletedJobsList',
    'QueuedJobsList', 'ScheduledJobsList', 'GetChoices', 'GetBasePath', 'Wait', 'DeleteJob'];

function JobsEdit($scope, $rootScope, $compile, $location, $log, $routeParams, JobForm, JobTemplateForm, GenerateForm, Rest,
    Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, RelatedPaginateInit, ReturnToCaller, ClearScope, InventoryList,
    CredentialList, ProjectList, LookUpInit, PromptPasswords, GetBasePath, md5Setup, FormatDate, JobStatusToolTip, Wait, Empty,
    ParseVariableString, GetChoices) {

    ClearScope();

    var defaultUrl = GetBasePath('jobs'),
        generator = GenerateForm,
        id = $routeParams.id,
        loadingFinishedCount = 0,
        templateForm = {},
        choicesCount = 0;

    generator.inject(JobForm, { mode: 'edit', related: true, scope: $scope });
    
    $scope.job_id = id;
    $scope.parseType = 'yaml';
    $scope.statusSearchSpin = false;
    $scope.disableParseSelection = true;

    function getPlaybooks(project, playbook) {
        if (!Empty(project)) {
            var url = GetBasePath('projects') + project + '/playbooks/';
            Rest.setUrl(url);
            Rest.get()
                .success(function (data) {
                    var i;
                    $scope.playbook_options = [];
                    for (i = 0; i < data.length; i++) {
                        $scope.playbook_options.push(data[i]);
                    }
                    for (i = 0; i < $scope.playbook_options.length; i++) {
                        if ($scope.playbook_options[i] === playbook) {
                            $scope.playbook = $scope.playbook_options[i];
                        }
                    }
                    $scope.$emit('jobTemplateLoadFinished');
                })
                .error(function () {
                    $scope.$emit('jobTemplateLoadFinished');
                });
        } else {
            $scope.$emit('jobTemplateLoadFinished');
        }
    }


    // Retrieve each related set and populate the playbook list
    if ($scope.jobLoadedRemove) {
        $scope.jobLoadedRemove();
    }
    $scope.jobLoadedRemove = $scope.$on('jobLoaded', function (e, related_cloud_credential, project, playbook) {

        getPlaybooks(project, playbook);
        if (related_cloud_credential) {
            //Get the name of the cloud credential
            Rest.setUrl(related_cloud_credential);
            Rest.get()
                .success(function (data) {
                    $scope.cloud_credential_name = data.name;
                    $scope.$emit('jobTemplateLoadFinished');
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to related cloud credential. GET returned status: ' + status });
                });
        } else {
            $scope.$emit('jobTemplateLoadFinished');
        }
        
    });

    // Turn off 'Wait' after both cloud credential and playbook list come back
    if ($scope.removeJobTemplateLoadFinished) {
        $scope.removeJobTemplateLoadFinished();
    }
    $scope.removeJobTemplateLoadFinished = $scope.$on('jobTemplateLoadFinished', function () {
        loadingFinishedCount++;
        if (loadingFinishedCount >= 2) {
            // The initial template load finished. Now load related jobs, which 
            // will turn off the 'working' spinner.
            Wait('stop');
        }
    });

    $scope.verbosity_options = [{
        value: 0,
        label: 'Default'
    }, {
        value: 1,
        label: 'Verbose'
    }, {
        value: 3,
        label: 'Debug'
    }];

    $scope.playbook_options = null;
    $scope.playbook = null;

    function calcRows(content) {
        var n = content.match(/\n/g),
            rows = (n) ? n.length : 1;
        return (rows > 15) ? 15 : rows;
    }

    if ($scope.removeLoadJobTemplate) {
        $scope.removeLoadJobTemplate();
    }
    $scope.removeLoadJobTemplate = $scope.$on('loadJobTemplate', function() {
        // Retrieve the job detail record and prepopulate the form
        Rest.setUrl(defaultUrl + ':id/');
        Rest.get({ params: { id: id } })
            .success(function (data) {
                
                var i, fld;
                
                LoadBreadCrumbs();
                
                $scope.status = data.status;
                $scope.created = FormatDate(data.created);
                $scope.modified = FormatDate(data.modified);
                $scope.result_stdout = data.result_stdout;
                $scope.result_traceback = data.result_traceback;
                $scope.stdout_rows = calcRows($scope.result_stdout);
                $scope.traceback_rows = calcRows($scope.result_traceback);
                $scope.job_explanation = data.job_explanation || 'Things may have ended badly or gone swimingly well';

                // Now load the job template form
                templateForm.addTitle = 'Create Job Templates';
                templateForm.editTitle = '{{ name }}';
                templateForm.name = 'job_templates';
                templateForm.twoColumns = true;
                templateForm.fields = angular.copy(JobTemplateForm.fields);
                for (fld in templateForm.fields) {
                    templateForm.fields[fld].readonly = true;
                }

                if (data.type === "playbook_run") {
                    $('#ui-accordion-jobs-collapse-0-panel-1').empty();
                    generator.inject(templateForm, {
                        mode: 'edit',
                        id: 'ui-accordion-jobs-collapse-0-panel-1',
                        related: false,
                        scope: $scope,
                        breadCrumbs: false
                    });
                }
                else {
                    $('#ui-accordion-jobs-collapse-0-header-1').hide();
                    $('#ui-accordion-jobs-collapse-0-panel-1').empty().hide();
                    $('#jobs-collapse-0').accordion( "option", "collapsible", false );
                }

                for (fld in templateForm.fields) {
                    if (fld !== 'variables' && data[fld] !== null && data[fld] !== undefined) {
                        if (JobTemplateForm.fields[fld].type === 'select') {
                            if ($scope[fld + '_options'] && $scope[fld + '_options'].length > 0) {
                                for (i = 0; i < $scope[fld + '_options'].length; i++) {
                                    if (data[fld] === $scope[fld + '_options'][i].value) {
                                        $scope[fld] = $scope[fld + '_options'][i];
                                    }
                                }
                            } else {
                                $scope[fld] = data[fld];
                            }
                        } else {
                            $scope[fld] = data[fld];
                        }
                    }
                    if (fld === 'variables') {
                        $scope.variables = ParseVariableString(data.extra_vars);
                    }
                    if (JobTemplateForm.fields[fld].type === 'lookup' && data.summary_fields[JobTemplateForm.fields[fld].sourceModel]) {
                        $scope[JobTemplateForm.fields[fld].sourceModel + '_' + JobTemplateForm.fields[fld].sourceField] =
                            data.summary_fields[JobTemplateForm.fields[fld].sourceModel][JobTemplateForm.fields[fld].sourceField];
                    }
                }

                $scope.id = data.id;
                $scope.name = (data.summary_fields && data.summary_fields.job_template) ? data.summary_fields.job_template.name : '';
                $scope.statusToolTip = JobStatusToolTip(data.status);
                $scope.url = data.url;
                $scope.project = data.project;
                $scope.launch_type = data.launch_type;

                // set the type
                data.type = 'playbook_run';  //temporary
                $scope.type_choices.every( function(choice) {
                    if (choice.value === data.type) {
                        $scope.type = choice.label;
                        return false;
                    }
                    return true;
                });
                
                $scope.$emit('jobLoaded', data.related.cloud_credential, data.project, data.playbook);
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to retrieve job: ' + $routeParams.id + '. GET status: ' + status });
            });
    });

    Wait('start');

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
        choicesCount++;
        if (choicesCount === 2) {
            $scope.$emit('loadJobTemplate');
        }
    });

    GetChoices({
        scope: $scope,
        url: GetBasePath('jobs'),
        field: 'job_type',
        variable: 'job_type_options',
        callback: 'choicesReady'
    });

    /*GetChoices({
        scope: $scope,
        url: GetBasePath('jobs'),
        field: 'status',
        variable: 'status_choices',
        callback: 'choicesReady'
    });*/

    GetChoices({
        scope: $scope,
        url: '/static/sample/data/types/data.json',     //GetBasePath('jobs')
        field: 'type',
        variable: 'type_choices',
        callback: 'choicesReady'
    });

    $scope.refresh = function () {
        Wait('start');
        Rest.setUrl(defaultUrl + id + '/');
        Rest.get()
            .success(function (data) {
                $scope.status = data.status;
                $scope.result_stdout = data.result_stdout;
                $scope.result_traceback = data.result_traceback;
                $scope.stdout_rows = calcRows($scope.result_stdout);
                $scope.traceback_rows = calcRows($scope.result_traceback);
                Wait('stop');
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Attempt to load job failed. GET returned status: ' + status });
            });
    };

    $scope.jobSummary = function () {
        $location.path('/jobs/' + id + '/job_host_summaries');
    };

    $scope.jobEvents = function () {
        $location.path('/jobs/' + id + '/job_events');
    };
}

JobsEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'JobForm', 'JobTemplateForm',
    'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 'RelatedPaginateInit',
    'ReturnToCaller', 'ClearScope', 'InventoryList', 'CredentialList', 'ProjectList', 'LookUpInit', 'PromptPasswords',
    'GetBasePath', 'md5Setup', 'FormatDate', 'JobStatusToolTip', 'Wait', 'Empty', 'ParseVariableString', 'GetChoices'
];

