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

function JobsListController ($scope, $compile, $routeParams, ClearScope, Breadcrumbs, LoadBreadCrumbs, LoadSchedulesScope, LoadJobsScope, RunningJobsList, CompletedJobsList, QueuedJobsList,
    ScheduledJobsList, GetChoices, GetBasePath, Wait, Socket) {
    
    ClearScope();

    var e,
        completed_scope, running_scope, queued_scope, scheduled_scope,
        choicesCount = 0,
        listCount = 0,
        api_complete = false,
        event_socket,
        event_queue = [{"status":"pending","endpoint":"/socket.io/jobs","unified_job_id":4129,"event":"status_changed"}],
        expecting = 0,
        max_rows;

    event_socket =  Socket({
        scope: $scope,
        endpoint: "jobs"
    });
    
    event_socket.init();

    event_socket.on("status_changed", function(data) {
        if (api_complete) {
            processEvent(data);
        }
        else {
            event_queue.push(data);
        }
    });
    
    function processEvent(event) {
        expecting = 0;
        switch(event.status) {
            case 'running':
                if (!inList(running_scope[RunningJobsList.name], event.unified_job_id)) {
                    expecting = 2;
                    running_scope.search('running_job');
                    queued_scope.search('queued_job');
                }
                break;
            case 'new':
            case 'pending':
            case 'waiting':
                if (!inList(queued_scope[QueuedJobsList.name], event.unified_job_id)) {
                    expecting = 1;
                    queued_scope.search('queued_job');
                }
                break;
            case 'successful':
            case 'failed':
            case 'error':
            case 'canceled':
                if (!inList(completed_scope[CompletedJobsList.name], event.unified_job_id)) {
                    expecting = 2;
                    completed_scope.search('completed_job');
                    running_scope.search('running_job');
                }
                break;
        }
    }

    function inList(list, id) {
        var found = false;
        list.every( function(row) {
            if (row.id === id) {
                found = true;
                return false;
            }
            return true;
        });
        return found;
    }


    if ($scope.removeProcessQueue) {
        $scope.removeProcessQueue();
    }
    $scope.removeProcessQueue = $scope.$on('ProcessQueue', function() {
        var event;
        listCount=0;
        if (event_queue.length > 0) {
            //console.log('found queued events');
            event = event_queue[0];
            processEvent(event);
            event_queue.splice(0,1);
            if ($scope.removeListLoaded) {
                $scope.removeListLoaded();
            }
            $scope.removeListLoaded = $scope.$on('listLoaded', function() {
                listCount++;
                if (listCount === expecting) {
                    //console.log('checking for more events...');
                    $scope.$emit('ProcessQueue');
                }
            });
        }
        //else {
            //console.log('no more events');
        //}
    });

    LoadBreadCrumbs();

    // Add breadcrumbs
    e = angular.element(document.getElementById('breadcrumbs'));
    e.html(Breadcrumbs({ list: { editTitle: 'Jobs' } , mode: 'edit' }));
    $compile(e)($scope);

    if ($scope.removeListLoaded) {
        $scope.removeListLoaded();
    }
    $scope.removeListLoaded = $scope.$on('listLoaded', function() {
        listCount++;
        if (listCount === 4) {
            api_complete = true;
            $scope.$emit('ProcessQueue');
        }
    });

    // After all choices are ready, load up the lists and populate the page
    if ($scope.removeBuildJobsList) {
        $scope.removeBuildJobsList();
    }
    $scope.removeBuildJobsList = $scope.$on('buildJobsList', function() {
        var opt, search_params;

        if (CompletedJobsList.fields.type) {
            CompletedJobsList.fields.type.searchOptions = $scope.type_choices;
        }
        if (RunningJobsList.fields.type) {
            RunningJobsList.fields.type.searchOptions = $scope.type_choices;
        }
        if (QueuedJobsList.fields.type) {
            QueuedJobsList.fields.type.searchOptions = $scope.type_choices;
        }
        if ($routeParams.status) {
            search_params[CompletedJobsList.iterator + 'SearchField'] = 'status';
            search_params[CompletedJobsList.iterator + 'SelectShow'] = true;
            search_params[CompletedJobsList.iterator + 'SearchSelectOpts'] = CompletedJobsList.fields.status.searchOptions;
            search_params[CompletedJobsList.iterator + 'SearchFieldLabel'] = CompletedJobsList.fields.status.label.replace(/<br\>/g,' ');
            search_params[CompletedJobsList.iterator + 'SearchType'] = '';
            for (opt in CompletedJobsList.fields.status.searchOptions) {
                if (CompletedJobsList.fields.status.searchOptions[opt].value === $routeParams.status) {
                    search_params[CompletedJobsList.iterator + 'SearchSelectValue'] = CompletedJobsList.fields.status.searchOptions[opt];
                    break;
                }
            }
        }
        completed_scope = $scope.$new(true);
        completed_scope.showJobType = true;
        LoadJobsScope({
            parent_scope: $scope,
            scope: completed_scope,
            list: CompletedJobsList,
            id: 'completed-jobs',
            url: GetBasePath('unified_jobs') + '?or__status=successful&or__status=failed&or__status=error&or__status=canceled',
            searchParams: search_params,
            pageSize: max_rows
        });
        running_scope = $scope.$new(true);
        LoadJobsScope({
            parent_scope: $scope,
            scope: running_scope,
            list: RunningJobsList,
            id: 'active-jobs',
            url: GetBasePath('unified_jobs') + '?status=running',
            pageSize: max_rows
        });
        queued_scope = $scope.$new(true);
        LoadJobsScope({
            parent_scope: $scope,
            scope: queued_scope,
            list: QueuedJobsList,
            id: 'queued-jobs',
            url: GetBasePath('unified_jobs') + '?or__status=pending&or__status=waiting&or__status=new',
            pageSize: max_rows
        });
        scheduled_scope = $scope.$new(true);
        LoadSchedulesScope({
            parent_scope: $scope,
            scope: scheduled_scope,
            list: ScheduledJobsList,
            id: 'scheduled-jobs',
            url: GetBasePath('schedules') + '?next_run__isnull=false',
            pageSize: max_rows
        });

        /*$scope.refreshJobs = function() {
            queued_scope.search('queued_job');
            running_scope.search('running_job');
            completed_scope.search('completed_job');
            scheduled_scope.search('schedule');
        };*/

        $(window).resize(_.debounce(function() {
            resizeContainers();
        }, 500));
    });

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
        choicesCount++;
        if (choicesCount === 2) {
            setHeight();
            $scope.$emit('buildJobsList');
        }
    });

    Wait('start');

    GetChoices({
        scope: $scope,
        url: GetBasePath('unified_jobs'),
        field: 'status',
        variable: 'status_choices',
        callback: 'choicesReady'
    });
    
    GetChoices({
        scope: $scope,
        url: GetBasePath('unified_jobs'),
        field: 'type',
        variable: 'type_choices',
        callback: 'choicesReady'
    });

    // Set the height of each container and calc max number of rows containers can hold
    function setHeight() {
        var docw = $(document).width(),
            available_height,
            search_row, page_row, height, header, row_height;
        if (docw > 1240) {
            // customize the container height and # of rows based on available viewport height
            available_height = $(window).height() - $('.main-menu').outerHeight() - $('#main_tabs').outerHeight() - $('#breadcrumbs').outerHeight() - $('.site-footer').outerHeight() - 25;
            $('.jobs-list-container').each(function() {
                $(this).height(Math.floor(available_height / 2));
            });
            search_row = Math.max($('.search-row:eq(0)').outerHeight(), 50);
            page_row = Math.max($('.page-row:eq(0)').outerHeight(), 33);
            header = Math.max($('#completed_jobs_table thead').height(), 41);
            height = Math.floor(available_height / 2) - header - page_row - search_row - 15;
            row_height = (docw < 1415) ? 47 : 27;
            //$('.jobs-list-container tbody tr:eq(0)').height();  <-- only works if data is loaded
            max_rows = Math.floor(height / row_height);
        }
        else {
            // when width < 1240px put things back to their default state
            $('.jobs-list-container').each(function() {
                $(this).css({ 'height': 'auto' });
            });
            max_rows = 5;
        }
    }

    // Set container height and return the number of allowed rows
    function resizeContainers() {
        setHeight();
        completed_scope[CompletedJobsList.iterator + '_page_size'] = max_rows;
        completed_scope.changePageSize(CompletedJobsList.name, CompletedJobsList.iterator);
        running_scope[RunningJobsList.iterator + '_page_size'] = max_rows;
        running_scope.changePageSize(RunningJobsList.name, RunningJobsList.iterator);
        queued_scope[QueuedJobsList.iterator + '_page_size'] = max_rows;
        queued_scope.changePageSize(QueuedJobsList.name, QueuedJobsList.iterator);
        scheduled_scope[ScheduledJobsList.iterator + '_page_size'] = max_rows;
        scheduled_scope.changePageSize(ScheduledJobsList.name, ScheduledJobsList.iterator);
    }
}

JobsListController.$inject = [ '$scope', '$compile', '$routeParams', 'ClearScope', 'Breadcrumbs', 'LoadBreadCrumbs', 'LoadSchedulesScope', 'LoadJobsScope', 'RunningJobsList', 'CompletedJobsList',
    'QueuedJobsList', 'ScheduledJobsList', 'GetChoices', 'GetBasePath', 'Wait', 'Socket' ];

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
        url: GetBasePath('unified_jobs'),
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
        url: GetBasePath('unified_jobs'),   //'/static/sample/data/types/data.json'
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
    'GetBasePath', 'md5Setup', 'FormatDate', 'JobStatusToolTip', 'Wait', 'Empty', 'ParseVariableString', 'GetChoices',
    'LoadDialogPartial'
];

