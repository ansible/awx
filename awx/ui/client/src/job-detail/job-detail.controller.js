/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:JobDetail
 * @description This controller's for the Job Detail Page
*/

export default
    [   '$location', '$rootScope', '$filter', '$scope', '$compile', '$state', '$stateParams', '$log', 'ClearScope',
        'GetBasePath', 'Wait', 'ProcessErrors', 'SelectPlay', 'SelectTask', 'GetElapsed', 'JobIsFinished',
        'SetTaskStyles', 'DigestEvent', 'UpdateDOM', 'DeleteJob', 'InitiatePlaybookRun', 'LoadPlays', 'LoadTasks',
        'ParseVariableString', 'GetChoices', 'fieldChoices', 'fieldLabels', 'EditSchedule',
        'ParseTypeChange', 'JobDetailService',
        function(
            $location, $rootScope, $filter, $scope, $compile, $state, $stateParams, $log, ClearScope,
            GetBasePath, Wait, ProcessErrors, SelectPlay, SelectTask, GetElapsed, JobIsFinished,
            SetTaskStyles, DigestEvent, UpdateDOM, DeleteJob, InitiatePlaybookRun, LoadPlays, LoadTasks,
            ParseVariableString, GetChoices, fieldChoices, fieldLabels, EditSchedule,
            ParseTypeChange, JobDetailService
        ) {
            ClearScope();

            var job_id = $stateParams.id,
                scope = $scope,
                api_complete = false,
                refresh_count = 0,
                lastEventId = 0,
                verbosity_options,
                job_type_options;

            scope.plays = [];
            scope.parseType = 'yaml';
            scope.previousTaskFailed = false;
            $scope.stdoutFullScreen = false;

            scope.$watch('job_status', function(job_status) {
                if (job_status && job_status.explanation && job_status.explanation.split(":")[0] === "Previous Task Failed") {
                    scope.previousTaskFailed = true;
                    var taskObj = JSON.parse(job_status.explanation.substring(job_status.explanation.split(":")[0].length + 1));
                    // return a promise from the options request with the permission type choices (including adhoc) as a param
                    var fieldChoice = fieldChoices({
                        scope: $scope,
                        url: 'api/v1/unified_jobs/',
                        field: 'type'
                    });

                    // manipulate the choices from the options request to be set on
                    // scope and be usable by the list form
                    fieldChoice.then(function (choices) {
                        choices =
                            fieldLabels({
                                choices: choices
                            });
                        scope.explanation_fail_type = choices[taskObj.job_type];
                        scope.explanation_fail_name = taskObj.job_name;
                        scope.explanation_fail_id = taskObj.job_id;
                        scope.task_detail = scope.explanation_fail_type + " failed for " + scope.explanation_fail_name + " with ID " + scope.explanation_fail_id + ".";
                    });
                } else {
                    scope.previousTaskFailed = false;
                }
            }, true);

            scope.$watch('plays', function(plays) {
                for (var play in plays) {
                    if (plays[play].elapsed) {
                        plays[play].finishedTip = "Play completed at " + $filter("longDate")(plays[play].finished) + ".";
                    } else {
                        plays[play].finishedTip = "Play not completed.";
                    }
                }
            });
            scope.hosts = [];
            scope.tasks = [];
            scope.$watch('tasks', function(tasks) {
                for (var task in tasks) {
                    if (tasks[task].elapsed) {
                        tasks[task].finishedTip = "Task completed at " + $filter("longDate")(tasks[task].finished) + ".";
                    } else {
                        tasks[task].finishedTip = "Task not completed.";
                    }
                    if (tasks[task].successfulCount) {
                        tasks[task].successfulCountTip = tasks[task].successfulCount;
                        tasks[task].successfulCountTip += (tasks[task].successfulCount === 1) ? " host event was" : " host events were";
                        tasks[task].successfulCountTip += " ok.";
                    } else {
                        tasks[task].successfulCountTip = "No host events were ok.";
                    }
                    if (tasks[task].changedCount) {
                        tasks[task].changedCountTip = tasks[task].changedCount;
                        tasks[task].changedCountTip += (tasks[task].changedCount === 1) ? " host event" : " host events";
                        tasks[task].changedCountTip += " changed.";
                    } else {
                        tasks[task].changedCountTip = "No host events changed.";
                    }
                    if (tasks[task].skippedCount) {
                        tasks[task].skippedCountTip = tasks[task].skippedCount;
                        tasks[task].skippedCountTip += (tasks[task].skippedCount === 1) ? " host event was" : " hosts events were";
                        tasks[task].skippedCountTip += " skipped.";
                    } else {
                        tasks[task].skippedCountTip = "No host events were skipped.";
                    }
                    if (tasks[task].failedCount) {
                        tasks[task].failedCountTip = tasks[task].failedCount;
                        tasks[task].failedCountTip += (tasks[task].failedCount === 1) ? " host event" : " host events";
                        tasks[task].failedCountTip += " failed.";
                    } else {
                        tasks[task].failedCountTip = "No host events failed.";
                    }
                    if (tasks[task].unreachableCount) {
                        tasks[task].unreachableCountTip = tasks[task].unreachableCount;
                        tasks[task].unreachableCountTip += (tasks[task].unreachableCount === 1) ? " host event was" : " hosts events were";
                        tasks[task].unreachableCountTip += " unreachable.";
                    } else {
                        tasks[task].unreachableCountTip = "No host events were unreachable.";
                    }
                    if (tasks[task].missingCount) {
                        tasks[task].missingCountTip = tasks[task].missingCount;
                        tasks[task].missingCountTip += (tasks[task].missingCount === 1) ? " host event was" : " host events were";
                        tasks[task].missingCountTip += " missing.";
                    } else {
                        tasks[task].missingCountTip = "No host events were missing.";
                    }
                }
            });
            scope.hostResults = [];

            scope.hostResultsMaxRows = 200;
            scope.tasksMaxRows = 200;
            scope.playsMaxRows = 200;

            // Set the following to true when 'Loading...' message desired
            scope.playsLoading = true;
            scope.tasksLoading = true;
            scope.hostResultsLoading = true;

            // Turn on the 'Waiting...' message until events begin arriving
            scope.waiting = true;

            scope.liveEventProcessing = true;     // true while job is active and live events are arriving
            scope.pauseLiveEvents = false;        // control play/pause state of event processing

            scope.job_status = {};
            scope.job_id = job_id;
            scope.auto_scroll = false;

            scope.searchPlaysEnabled = true;
            scope.searchTasksEnabled = true;
            scope.searchHostsEnabled = true;
            scope.search_play_status = 'all';
            scope.search_task_status = 'all';
            scope.search_host_status = 'all';

            scope.haltEventQueue = false;
            scope.processing = false;
            scope.lessStatus = false;
            scope.lessDetail = false;
            // pops the event summary panel open if we're in the host summary child state
            //scope.lessEvents = ($state.current.name === 'jobDetail.host-summary' || $state.current.name === 'jobDetail.host-events') ? false : true;
            if ($state.current.name === 'jobDetail.host-summary' ){
                scope.lessEvents = false;
            }
            else{
                scope.lessEvents = true;
            }
            scope.jobData = {};
            scope.jobData.hostSummaries = {};

            verbosity_options = [
                { value: 0, label: 'Default' },
                { value: 1, label: 'Verbose' },
                { value: 3, label: 'Debug' }
            ];

            job_type_options = [
                { value: 'run', label: 'Run' },
                { value: 'check', label: 'Check' }
            ];

            GetChoices({
                scope: scope,
                url: GetBasePath('unified_jobs'),
                field: 'status',
                variable: 'status_choices',
            });

            scope.eventsHelpText = "<p><i class=\"fa fa-circle successful-hosts-color\"></i> Successful</p>\n" +
                "<p><i class=\"fa fa-circle changed-hosts-color\"></i> Changed</p>\n" +
                "<p><i class=\"fa fa-circle unreachable-hosts-color\"></i> Unreachable</p>\n" +
                "<p><i class=\"fa fa-circle failed-hosts-color\"></i> Failed</p>\n";
            function openSocket() {
                $rootScope.event_socket.on("job_events-" + job_id, function(data) {
                    // update elapsed time on each event received
                    scope.job_status.elapsed = GetElapsed({
                        start: scope.job.created,
                        end: Date.now()
                    });
                    if (api_complete && data.id > lastEventId) {
                        scope.waiting = false;
                        data.event = data.event_name;
                        DigestEvent({ scope: scope, event: data });
                    }
                    UpdateDOM({ scope: scope });
                });
                // Unbind $rootScope socket event binding(s) so that they don't get triggered
                // in another instance of this controller
                scope.$on('$destroy', function() {
                    $rootScope.event_socket.removeAllListeners("job_events-" + job_id);
                });
            }
            openSocket();

            if ($rootScope.removeJobStatusChange) {
                $rootScope.removeJobStatusChange();
            }
            $rootScope.removeJobStatusChange = $rootScope.$on('JobStatusChange-jobDetails', function(e, data) {
                // if we receive a status change event for the current job indicating the job
                // is finished, stop event queue processing and reload
                if (parseInt(data.unified_job_id, 10) === parseInt(job_id,10)) {
                    if (data.status === 'failed' || data.status === 'canceled' ||
                            data.status === 'error' || data.status === 'successful' || data.status === 'running') {
                        $scope.liveEventProcessing = false;
                        if (!scope.pauseLiveEvents) {
                            $scope.$emit('LoadJob'); //this is what is used for the refresh
                        }
                    }
                }
            });

            if ($rootScope.removeJobSummaryComplete) {
                $rootScope.removeJobSummaryComplete();
            }
            $rootScope.removeJobSummaryComplete = $rootScope.$on('JobSummaryComplete', function() {
                // the job host summary should now be available from the API
                $log.debug('Trigging reload of job_host_summaries');
                scope.$emit('InitialLoadComplete');
            });

            if (scope.removeInitialLoadComplete) {
                scope.removeInitialLoadComplete();
            }
            scope.removeInitialLoadComplete = scope.$on('InitialLoadComplete', function() {
                Wait('stop');

                if (JobIsFinished(scope)) {
                    scope.liveEventProcessing = false; // signal that event processing is over and endless scroll
                    scope.pauseLiveEvents = false;      // should be enabled
                    var params = {
                        event: 'playbook_on_stats'
                    };
                    JobDetailService.getRelatedJobEvents(scope.job.id, params)
                        .success(function() {
                            UpdateDOM({ scope: scope });
                        })
                        .error(function(data, status) {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call failed. GET returned: ' + status });
                        });
                    $log.debug('Job completed!');
                    $log.debug(scope.jobData);
                }
                else {
                    api_complete = true;  //trigger events to start processing
                    UpdateDOM({ scope: scope});
                }
            });

            if (scope.removeLoadHosts) {
                scope.removeLoadHosts();
            }
            scope.removeLoadHosts = scope.$on('LoadHosts', function() {
                if (scope.activeTask) {

                    var play = scope.jobData.plays[scope.activePlay],
                        task;
                    if(play){
                      task = play.tasks[scope.activeTask];
                    }
                    if (play && task) {
                        var params = {
                            parent: task.id,
                            event__startswith: 'runner',
                            page_size: scope.hostResultsMaxRows
                        };
                        JobDetailService.getRelatedJobEvents(scope.job.id, params)
                            .success(function(data) {
                                if (data.results.length > 0) {
                                    lastEventId =  data.results[0].id;
                                }
                                scope.next_host_results = data.next;
                                task.hostResults = JobDetailService.processHostEvents(data.results);
                                scope.$emit('InitialLoadComplete');
                            });
                    } else {
                        scope.$emit('InitialLoadComplete');
                    }
                } else {
                scope.$emit('InitialLoadComplete');
                }
            });

            if (scope.removeLoadTasks) {
                scope.removeLoadTasks();
            }
            scope.removeLoadTasks = scope.$on('LoadTasks', function() {
                if (scope.activePlay) {
                    var play = scope.jobData.plays[scope.activePlay];

                    if (play) {
                        var params = {
                            event_id: play.id,
                            page_size: scope.tasksMaxRows,
                            order: 'id'
                        };
                        JobDetailService.getJobTasks(scope.job.id, params)
                            .success(function(data) {
                                scope.next_tasks = data.next;
                                if (data.results.length > 0) {
                                    lastEventId = data.results[data.results.length - 1].id;
                                    if (scope.liveEventProcessing) {
                                        scope.activeTask = data.results[data.results.length - 1].id;
                                    }
                                    else {
                                        scope.activeTask = data.results[0].id;
                                    }
                                    scope.selectedTask = scope.activeTask;
                                }
                                data.results.forEach(function(event, idx) {
                                    var end, elapsed, status, status_text;

                                    if (play.firstTask === undefined  || play.firstTask === null) {
                                        play.firstTask = event.id;
                                        play.hostCount = (event.host_count) ? event.host_count : 0;
                                    }

                                    if (idx < data.results.length - 1) {
                                        // end date = starting date of the next event
                                        end = data.results[idx + 1].created;
                                    }
                                    else {
                                        // no next event (task), get the end time of the play
                                        if(scope.jobData.plays[scope.activePlay]){
                                            end = scope.jobData.plays[scope.activePlay].finished;
                                        }
                                    }

                                    if (end) {
                                        elapsed = GetElapsed({
                                            start: event.created,
                                            end: end
                                        });
                                    }
                                    else {
                                        elapsed = '00:00:00';
                                    }

                                    status = (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful';
                                    status_text = (event.failed) ? 'Failed' : (event.changed) ? 'Changed' : 'OK';

                                    play.tasks[event.id] = {
                                        id: event.id,
                                        play_id: scope.activePlay,
                                        name: event.name,
                                        status: status,
                                        status_text: status_text,
                                        status_tip: "Event ID: " + event.id + "<br />Status: " + status_text,
                                        created: event.created,
                                        modified: event.modified,
                                        finished: end,
                                        elapsed: elapsed,
                                        hostCount: (event.host_count) ? event.host_count : 0,
                                        reportedHosts: (event.reported_hosts) ? event.reported_hosts : 0,
                                        successfulCount: (event.successful_count) ? event.successful_count : 0,
                                        failedCount: (event.failed_count) ? event.failed_count : 0,
                                        changedCount: (event.changed_count) ? event.changed_count : 0,
                                        skippedCount: (event.skipped_count) ? event.skipped_count : 0,
                                        unreachableCount: (event.unreachable_count) ? event.unreachable_count : 0,
                                        taskActiveClass: '',
                                        hostResults: {}
                                    };
                                    if (play.firstTask !== event.id) {
                                        // this is not the first task
                                        play.tasks[event.id].hostCount = play.tasks[play.firstTask].hostCount;
                                    }
                                    if (play.tasks[event.id].reportedHosts === 0 && play.tasks[event.id].successfulCount === 0 &&
                                        play.tasks[event.id].failedCount === 0 && play.tasks[event.id].changedCount === 0 &&
                                        play.tasks[event.id].skippedCount === 0 && play.tasks[event.id].unreachableCount === 0) {
                                        play.tasks[event.id].status = 'no-matching-hosts';
                                        play.tasks[event.id].status_text = 'No matching hosts';
                                        play.tasks[event.id].status_tip = "Event ID: " + event.id + "<br />Status: No matching hosts";
                                    }
                                    play.taskCount++;
                                    SetTaskStyles({
                                        task: play.tasks[event.id]
                                    });
                                });
                                if (scope.activeTask && scope.jobData.plays[scope.activePlay] && scope.jobData.plays[scope.activePlay].tasks[scope.activeTask]) {
                                    scope.jobData.plays[scope.activePlay].tasks[scope.activeTask].taskActiveClass = 'JobDetail-tableRow--selected';
                                }
                                scope.$emit('LoadHosts');
                            })
                            .error(function(data) {
                                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                    msg: 'Call failed. GET returned: ' + status });
                            });
                    } else {
                        scope.$emit('InitialLoadComplete');
                    }
                } else {
                        scope.$emit('InitialLoadComplete');
                }
            });

            if (scope.removeLoadPlays) {
                scope.removeLoadPlays();
            }
            scope.removeLoadPlays = scope.$on('LoadPlays', function(e, events_url) {
                scope.jobData.plays = {};
                var params = {
                    order_by: 'id'
                };
                if (scope.job.summary_fields.unified_job_template.unified_job_type === 'job'){
                    JobDetailService.getJobPlays(scope.job.id, params)
                    .success( function(data) {
                        scope.next_plays = data.next;
                        if (data.results.length > 0) {
                            lastEventId = data.results[data.results.length - 1].id;
                            if (scope.liveEventProcessing) {
                                scope.activePlay = data.results[data.results.length - 1].id;
                            }
                            else {
                                scope.activePlay = data.results[0].id;
                            }
                            scope.selectedPlay = scope.activePlay;
                        } else {
                            // if we are here, there are no plays and the job has failed, let the user know they may want to consult stdout
                            if ( (scope.job_status.status === 'failed' || scope.job_status.status === 'error') &&
                                (!scope.job_status.explanation)) {
                                scope.job_status.explanation = "See standard out for more details";
                            }
                        }
                        data.results.forEach(function(event, idx) {
                            var status, status_text, start, end, elapsed, ok, changed, failed, skipped;

                            status = (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful';
                            status_text = (event.failed) ? 'Failed' : (event.changed) ? 'Changed' : 'OK';
                            start = event.started;

                            if (idx < data.results.length - 1) {
                                // end date = starting date of the next event
                                end = data.results[idx + 1].started;
                            }
                            else if (JobIsFinished(scope)) {
                                // this is the last play and the job already finished
                                end = scope.job_status.finished;
                            }
                            if (end) {
                                elapsed = GetElapsed({
                                    start: start,
                                    end: end
                                });
                            }
                            else {
                                elapsed = '00:00:00';
                            }

                            scope.jobData.plays[event.id] = {
                                id: event.id,
                                name: event.play,
                                created: start,
                                finished: end,
                                status: status,
                                status_text: status_text,
                                status_tip: "Event ID: " + event.id + "<br />Status: " + status_text,
                                elapsed: elapsed,
                                hostCount: 0,
                                fistTask: null,
                                taskCount: 0,
                                playActiveClass: '',
                                unreachableCount: (event.unreachable_count) ? event.unreachable_count : 0,
                                tasks: {}
                            };

                            ok = (event.ok_count) ? event.ok_count : 0;
                            changed = (event.changed_count) ? event.changed_count : 0;
                            failed = (event.failed_count) ? event.failed_count : 0;
                            skipped = (event.skipped_count) ? event.skipped_count : 0;

                            scope.jobData.plays[event.id].hostCount = ok + changed + failed + skipped;

                            if (scope.jobData.plays[event.id].hostCount > 0 || event.unreachable_count > 0 || scope.job_status.status === 'successful' ||
                                scope.job_status.status === 'failed' || scope.job_status.status === 'error' || scope.job_status.status === 'canceled') {
                                // force the play to be on the 'active' list
                                scope.jobData.plays[event.id].taskCount = 1;
                            }

                            if (scope.jobData.plays[event.id].hostCount === 0 && event.unreachable_count === 0) {
                                scope.jobData.plays[event.id].status = 'no-matching-hosts';
                                scope.jobData.plays[event.id].status_text = 'No matching hosts';
                                scope.jobData.plays[event.id].status_tip = "Event ID: " + event.id + "<br />Status: No matching hosts";
                            }
                        });
                        if (scope.activePlay && scope.jobData.plays[scope.activePlay]) {
                            scope.jobData.plays[scope.activePlay].playActiveClass = 'JobDetail-tableRow--selected';
                        }
                        scope.$emit('LoadTasks', events_url);
                    });
                }
            });


            if (scope.removeLoadJob) {
                scope.removeLoadJob();
            }
            scope.removeLoadJobRow = scope.$on('LoadJob', function() {
                Wait('start');
                scope.job_status = {};

                scope.playsLoading = true;
                scope.tasksLoading = true;
                scope.hostResultsLoading = true;

                // Load the job record
                JobDetailService.getJob({id: job_id})
                    .success(function(res) {
                        var i,
                            data = res.results[0];
                        scope.job = data;
                        scope.job_template_name = data.name;
                        scope.project_name = (data.summary_fields.project) ? data.summary_fields.project.name : '';
                        scope.inventory_name = (data.summary_fields.inventory) ? data.summary_fields.inventory.name : '';
                        scope.job_template_url = '/#/job_templates/' + data.unified_job_template;
                        scope.inventory_url = (scope.inventory_name && data.inventory) ? '/#/inventories/' + data.inventory : '';
                        scope.project_url = (scope.project_name && data.project) ? '/#/projects/' + data.project : '';
                        scope.credential_url = (data.credential) ? '/#/credentials/' + data.credential : '';
                        scope.cloud_credential_url = (data.cloud_credential) ? '/#/credentials/' + data.cloud_credential : '';
                        scope.playbook = data.playbook;
                        scope.credential = data.credential;
                        scope.cloud_credential = data.cloud_credential;
                        scope.forks = data.forks;
                        scope.limit = data.limit;
                        scope.verbosity = data.verbosity;
                        scope.job_tags = data.job_tags;
                        scope.variables = ParseVariableString(data.extra_vars);

                        // If we get created_by back from the server then use it.  This means that the job was kicked
                        // off by a user and not a schedule AND that the user still exists in the system.
                        if(data.summary_fields.created_by) {
                            scope.users_url = '/#/users/' + data.summary_fields.created_by.id;
                            scope.created_by = data.summary_fields.created_by.username;
                        }
                        else {
                            if(data.summary_fields.schedule) {
                                // Build the Launched By link to point to the schedule that kicked it off
                                scope.scheduled_by = (data.summary_fields.schedule.name) ? data.summary_fields.schedule.name.toString() : '';
                            }
                            // If there is no schedule or created_by then we can assume that the job was
                            // created by a deleted user
                        }

                        if (data.summary_fields.credential) {
                                scope.credential_name = data.summary_fields.credential.name;
                                scope.credential_url = data.related.credential
                                    .replace('api/v1', '#');
                        } else {
                            scope.credential_name = "";
                        }

                        if (data.summary_fields.cloud_credential) {
                                scope.cloud_credential_name = data.summary_fields.cloud_credential.name;
                                scope.cloud_credential_url = data.related.cloud_credential
                            .replace('api/v1', '#');
                        } else {
                            scope.cloud_credential_name = "";
                        }

                        for (i=0; i < verbosity_options.length; i++) {
                            if (verbosity_options[i].value === data.verbosity) {
                                scope.verbosity = verbosity_options[i].label;
                            }
                        }

                        for (i=0; i < job_type_options.length; i++) {
                            if (job_type_options[i].value === data.job_type) {
                                scope.job_type = job_type_options[i].label;
                            }
                        }

                        // In the case the job is already completed, or an error already happened,
                        // populate scope.job_status info
                        scope.job_status.status = (data.status === 'waiting' || data.status === 'new') ? 'pending' : data.status;
                        scope.job_status.started = data.started;
                        scope.job_status.status_class = ((data.status === 'error' || data.status === 'failed') && data.job_explanation) ? "alert alert-danger" : "";
                        scope.job_status.explanation = data.job_explanation;
                        if(data.result_traceback) {
                            scope.job_status.traceback = data.result_traceback.trim().split('\n').join('<br />');
                        }
                        if (data.status === 'successful' || data.status === 'failed' || data.status === 'error' || data.status === 'canceled') {
                            scope.job_status.finished = data.finished;
                            scope.liveEventProcessing = false;
                            scope.pauseLiveEvents = false;
                            scope.waiting = false;
                            scope.playsLoading = false;
                            scope.tasksLoading = false;
                            scope.hostResultsLoading = false;
                        }
                        else {
                            scope.job_status.finished = null;
                        }

                        if (data.started && data.finished) {
                            scope.job_status.elapsed = GetElapsed({
                                start: data.started,
                                end: data.finished
                            });
                        }
                        else {
                            scope.job_status.elapsed = '00:00:00';
                        }
                        scope.status_choices.every(function(status) {
                               if (status.value === scope.job.status) {
                                   scope.job_status.status_label = status.label;
                                   return false;
                               }
                               return true;
                           });
                        //scope.setSearchAll('host');
                        ParseTypeChange({ scope: scope, field_id: 'pre-formatted-variables' });
                        scope.$emit('LoadPlays', data.related.job_events);
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to retrieve job: ' + $stateParams.id + '. GET returned: ' + status });
                    });
            });


            if (scope.removeRefreshCompleted) {
                scope.removeRefreshCompleted();
            }
            scope.removeRefreshCompleted = scope.$on('RefreshCompleted', function() {
                refresh_count++;
                if (refresh_count === 1) {
                    // First time. User just loaded page.
                    scope.$emit('LoadJob');
                }
            });

            scope.adjustSize = function() {
                var height, ww = $(window).width();
                if (ww < 1024) {
                    $('#job-summary-container').hide();
                    $('#job-detail-container').css({ "width": "100%", "padding-right": "15px" });
                    $('#summary-button').show();
                }
                else {
                    $('.overlay').hide();
                    $('#summary-button').hide();
                    $('#hide-summary-button').hide();
                    $('#job-summary-container .job_well').css({
                        'box-shadow': 'none',
                        'height': 'auto'
                    });
                    $('#job-summary-container').css({
                        "width": "41.66666667%",
                        "padding-left": "7px",
                        "padding-right": "15px",
                        "z-index": 0
                    });
                    setTimeout(function() { $('#job-summary-container .job_well').height($('#job-detail-container').height() - 18); }, 500);
                    $('#job-summary-container').show();
                }

                scope.lessStatus = false; // close the view more status option


                height = $(window).height() - $('#main-menu-container .navbar').outerHeight() -
                    $('#job-detail-container').outerHeight() - 20;
                scope.$emit('RefreshCompleted');
            };

            setTimeout(function() { scope.adjustSize(); }, 500);

            // Use debounce for the underscore library to adjust after user resizes window.
            $(window).resize(_.debounce(function(){
                scope.adjustSize();
            }, 500));

            function flashPlayTip() {
                setTimeout(function(){
                    $('#play-help').popover('show');
                },500);
                setTimeout(function() {
                    $('#play-help').popover('hide');
                }, 5000);
            }

            scope.selectPlay = function(id) {
                if (scope.liveEventProcessing && !scope.pauseLiveEvents) {
                    scope.pauseLiveEvents = true;
                    flashPlayTip();
                }
                SelectPlay({
                    scope: scope,
                    id: id
                });
            };

            scope.selectTask = function(id) {
                if (scope.liveEventProcessing && !scope.pauseLiveEvents) {
                    scope.pauseLiveEvents = true;
                    flashPlayTip();
                }
                SelectTask({
                    scope: scope,
                    id: id
                });
            };

            scope.togglePlayButton = function() {
                if (scope.pauseLiveEvents) {
                    scope.pauseLiveEvents = false;
                    scope.$emit('LoadJob');
                }
            };

            scope.objectIsEmpty = function(obj) {
                if (angular.isObject(obj)) {
                    return (Object.keys(obj).length > 0) ? false : true;
                }
                return true;
            };

            scope.toggleLessEvents = function() {
                if (!scope.lessEvents) {
                    $('#events-summary').slideUp(0);
                    scope.lessEvents = true;
                }
                else {
                    $('#events-summary').slideDown(0);
                    scope.lessEvents = false;
                }
            };

            scope.toggleLessStatus = function() {
                if (!scope.lessStatus) {
                    $('#job-status-form').slideUp(200);
                    scope.lessStatus = true;
                }
                else {
                    $('#job-status-form').slideDown(200);
                    scope.lessStatus = false;
                }
            };

            scope.toggleLessDetail = function() {
                if (!scope.lessDetail) {
                    $('#job-detail-details').slideUp(200);
                    scope.lessDetail = true;
                }
                else {
                    $('#job-detail-details').slideDown(200);
                    scope.lessDetail = false;
                }
            };

            scope.filterTaskStatus = function() {
                scope.search_task_status = (scope.search_task_status === 'all') ? 'failed' : 'all';
                if (!scope.liveEventProcessing || scope.pauseLiveEvents) {
                    LoadTasks({
                        scope: scope
                    });
                }
            };

            scope.filterPlayStatus = function() {
                scope.search_play_status = (scope.search_play_status === 'all') ? 'failed' : 'all';
                if (!scope.liveEventProcessing || scope.pauseLiveEvents) {
                    LoadPlays({
                        scope: scope
                    });
                }
            };

            scope.filterHostStatus = function(){
                scope.search_host_status = (scope.search_host_status === 'all') ? 'failed' : 'all';
                if (!scope.liveEventProcessing || scope.pauseLiveEvents){
                    if (scope.selectedTask !== null && scope.selectedPlay !== null){
                        var params = {
                            parent: scope.selectedTask,
                            page_size: scope.hostResultsMaxRows,
                            order: 'host_name,counter',
                        };
                        if (scope.search_host_status === 'failed'){
                            params.failed = true;
                        }
                        JobDetailService.getRelatedJobEvents(scope.job.id, params).success(function(res){
                            scope.hostResults = JobDetailService.processHostEvents(res.results);
                            scope.hostResultsLoading = false;
                        });
                    }
                }
            };

            scope.searchPlays = function() {
                if (scope.search_play_name) {
                    scope.searchPlaysEnabled = false;
                }
                else {
                    scope.searchPlaysEnabled = true;
                }
                if (!scope.liveEventProcessing || scope.pauseLiveEvents) {
                    LoadPlays({
                        scope: scope
                    });
                }
            };

            scope.searchPlaysKeyPress = function(e) {
                if (e.keyCode === 13) {
                    scope.searchPlays();
                    e.stopPropagation();
                }
            };

            scope.searchTasks = function() {
                var params;
                if (scope.search_task_name) {
                    scope.searchTasksEnabled = false;
                }
                else {
                    scope.searchTasksEnabled = true;
                }
                if (!scope.liveEventProcessing || scope.pauseLiveEvents) {
                    if (scope.search_task_status === 'failed'){
                        params.failed = true;
                    }
                    LoadTasks({
                        scope: scope
                    });
                }
            };

            scope.searchTasksKeyPress = function(e) {
                if (e.keyCode === 13) {
                    scope.searchTasks();
                    e.stopPropagation();
                }
            };

            scope.searchHosts = function() {
                var params;
                if (scope.search_host_name) {
                    scope.searchHostsEnabled = false;
                }
                else {
                    scope.searchHostsEnabled = true;
                }
                if (!scope.liveEventProcessing || scope.pauseLiveEvents) {
                    scope.hostResultsLoading = true;
                    params = {
                        parent: scope.selectedTask,
                        event__startswith: 'runner',
                        page_size: scope.hostResultsMaxRows,
                        order: 'host_name,counter',
                        host_name__icontains: scope.search_host_name
                    };
                    if (scope.search_host_status === 'failed'){
                        params.failed = true;
                    }
                    JobDetailService.getRelatedJobEvents(scope.job.id, params).success(function(res){
                        scope.hostResults = JobDetailService.processHostEvents(res.results);
                        scope.hostResultsLoading = false;
                    });
                }
            };


            if (scope.removeDeleteFinished) {
                scope.removeDeleteFinished();
            }
            scope.removeDeleteFinished = scope.$on('DeleteFinished', function(e, action) {
                Wait('stop');
                if (action !== 'cancel') {
                    Wait('stop');
                    $location.url('/jobs');
                }
            });

            scope.deleteJob = function() {
                DeleteJob({
                    scope: scope,
                    id: scope.job.id,
                    job: scope.job,
                    callback: 'DeleteFinished'
                });
            };

            scope.relaunchJob = function() {
                InitiatePlaybookRun({
                    scope: scope,
                    id: scope.job.id
                });
            };

            scope.playsScrollDown = function() {
                // check for more plays when user scrolls to bottom of play list...
                if (((!scope.liveEventProcessing) || (scope.liveEventProcessing && scope.pauseLiveEvents)) && scope.next_plays) {
                    $('#playsMoreRows').fadeIn();
                    scope.playsLoading = true;
                    JobDetailService.getNextPage(scope.next_plays)
                        .success( function(data) {
                            scope.next_plays = data.next;
                            data.results.forEach(function(event, idx) {
                                var status, status_text, start, end, elapsed, ok, changed, failed, skipped;

                                status = (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful';
                                status_text = (event.failed) ? 'Failed' : (event.changed) ? 'Changed' : 'OK';
                                start = event.started;

                                if (idx < data.results.length - 1) {
                                    // end date = starting date of the next event
                                    end = data.results[idx + 1].started;
                                }
                                else if (JobIsFinished(scope)) {
                                    // this is the last play and the job already finished
                                    end = scope.job_status.finished;
                                }
                                if (end) {
                                    elapsed = GetElapsed({
                                        start: start,
                                        end: end
                                    });
                                }
                                else {
                                    elapsed = '00:00:00';
                                }

                                scope.plays.push({
                                    id: event.id,
                                    name: event.play,
                                    created: start,
                                    finished: end,
                                    status: status,
                                    status_text: status_text,
                                    status_tip: "Event ID: " + event.id + "<br />Status: " + status_text,
                                    elapsed: elapsed,
                                    hostCount: 0,
                                    fistTask: null,
                                    playActiveClass: '',
                                    unreachableCount: (event.unreachable_count) ? event.unreachable_count : 0,
                                });

                                ok = (event.ok_count) ? event.ok_count : 0;
                                changed = (event.changed_count) ? event.changed_count : 0;
                                failed = (event.failed_count) ? event.failed_count : 0;
                                skipped = (event.skipped_count) ? event.skipped_count : 0;

                                scope.plays[scope.plays.length - 1].hostCount = ok + changed + failed + skipped;
                                scope.playsLoading = false;
                            });
                            $('#playsMoreRows').fadeOut(400);
                        })
                        .error( function(data, status) {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call to ' + scope.next_plays + '. GET returned: ' + status });
                        });
                }
            };

            scope.tasksScrollDown = function() {
                // check for more tasks when user scrolls to bottom of task list...
                if (((!scope.liveEventProcessing) || (scope.liveEventProcessing && scope.pauseLiveEvents)) && scope.next_tasks) {
                    $('#tasksMoreRows').fadeIn();
                    scope.tasksLoading = true;
                    JobDetailService.getNextPage(scope.next_tasks)
                        .success(function(data) {
                            scope.next_tasks = data.next;
                            data.results.forEach(function(event, idx) {
                                var end, elapsed, status, status_text;
                                if (idx < data.results.length - 1) {
                                    // end date = starting date of the next event
                                    end = data.results[idx + 1].created;
                                }
                                else {
                                    // no next event (task), get the end time of the play
                                    scope.plays.every(function(p, j) {
                                        if (p.id === scope.selectedPlay) {
                                            end = scope.plays[j].finished;
                                            return false;
                                        }
                                        return true;
                                    });
                                }
                                if (end) {
                                    elapsed = GetElapsed({
                                        start: event.created,
                                        end: end
                                    });
                                }
                                else {
                                    elapsed = '00:00:00';
                                }

                                status = (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful';
                                status_text = (event.failed) ? 'Failed' : (event.changed) ? 'Changed' : 'OK';

                                scope.tasks.push({
                                    id: event.id,
                                    play_id: scope.selectedPlay,
                                    name: event.name,
                                    status: status,
                                    status_text: status_text,
                                    status_tip: "Event ID: " + event.id + "<br />Status: " + status_text,
                                    created: event.created,
                                    modified: event.modified,
                                    finished: end,
                                    elapsed: elapsed,
                                    hostCount: event.host_count,          // hostCount,
                                    reportedHosts: event.reported_hosts,
                                    successfulCount: event.successful_count,
                                    failedCount: event.failed_count,
                                    changedCount: event.changed_count,
                                    skippedCount: event.skipped_count,
                                    taskActiveClass: ''
                                });
                                SetTaskStyles({
                                    task: scope.tasks[scope.tasks.length - 1]
                                });
                            });
                            $('#tasksMoreRows').fadeOut(400);
                            scope.tasksLoading = false;
                        })
                        .error(function(data, status) {
                            $('#tasksMoreRows').fadeOut(400);
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call to ' + scope.next_tasks + '. GET returned: ' + status });
                        });
                }
            };

            scope.hostResultsScrollDown = function() {
                // check for more hosts when user scrolls to bottom of host results list...
                if (((!scope.liveEventProcessing) || (scope.liveEventProcessing && scope.pauseLiveEvents)) && scope.next_host_results) {
                    $('#hostResultsMoreRows').fadeIn();
                    scope.hostResultsLoading = true;
                    JobDetailService.getNextPage(scope.next_host_results)
                        .success(function(data) {
                            scope.next_host_results = data.next;
                            data.results.forEach(function(row) {
                                var status, status_text, item, msg;
                                if (row.event === "runner_on_skipped") {
                                    status = 'skipped';
                                }
                                else if (row.event === "runner_on_unreachable") {
                                    status = 'unreachable';
                                }
                                else {
                                    status = (row.failed) ? 'failed' : (row.changed) ? 'changed' : 'successful';
                                }
                                switch(status) {
                                    case "successful":
                                        status_text = 'OK';
                                        break;
                                    case "changed":
                                        status_text = "Changed";
                                        break;
                                    case "failed":
                                        status_text = "Failed";
                                        break;
                                    case "unreachable":
                                        status_text = "Unreachable";
                                        break;
                                    case "skipped":
                                        status_text = "Skipped";
                                }
                                if (row.event_data && row.event_data.res) {
                                    item = row.event_data.res.item;
                                    if (typeof item === "object") {
                                        item = JSON.stringify(item);
                                    }
                                }
                                msg = '';
                                if (row.event_data && row.event_data.res) {
                                    if (typeof row.event_data.res === 'object') {
                                        msg = row.event_data.res.msg;
                                    } else {
                                        msg = row.event_data.res;
                                    }
                                }
                                scope.hostResults.push({
                                    id: row.id,
                                    status: status,
                                    status_text: status_text,
                                    host_id: row.host,
                                    task_id: row.parent,
                                    name: row.event_data.host,
                                    created: row.created,
                                    msg: (row.event_data && row.event_data.res) ? row.event_data.res.msg : '',
                                    item: item
                                });
                                scope.hostResultsLoading = false;
                            });
                            $('#hostResultsMoreRows').fadeOut(400);
                        })
                        .error(function(data, status) {
                            $('#hostResultsMoreRows').fadeOut(400);
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call to ' + scope.next_host_results + '. GET returned: ' + status });
                        });
                }
            };

            scope.refresh = function(){
                $scope.$emit('LoadJob');
            };

            // Click binding for the expand/collapse button on the standard out log
            $scope.toggleStdoutFullscreen = function() {
                $scope.stdoutFullScreen = !$scope.stdoutFullScreen;
            };

            scope.editSchedule = function() {
            	// We need to get the schedule's ID out of the related links
            	// An example of the related schedule link looks like /api/v1/schedules/5
            	// where 5 is the ID we are trying to capture
                var regex = /\/api\/v1\/schedules\/(\d+)\//;
                var id = scope.job.related.schedule.match(regex)[1];
                if (id) {
                	// If we get an ID from the regular expression go ahead and open up the
                	// modal via the EditSchedule service
                    EditSchedule({
                        scope: scope,
                        id: parseInt(id),
                        callback: 'SchedulesRefresh'
                    });
                }
            };

            // SchedulesRefresh is the callback string that we passed to the edit schedule modal
            // When the modal successfully updates the schedule it will emit this event and pass
            // the updated schedule object
            if (scope.removeSchedulesRefresh) {
                scope.removeSchedulesRefresh();
            }
            scope.$on('SchedulesRefresh', function(e, data) {
                if (data) {
                    scope.scheduled_by = data.name;
                }
            });
        }
];
