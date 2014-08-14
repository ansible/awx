/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobDetail.js
 *
 */

'use strict';

function JobDetailController ($location, $rootScope, $scope, $compile, $routeParams, $log, ClearScope, Breadcrumbs, LoadBreadCrumbs, GetBasePath, Wait, Rest,
    ProcessErrors, SelectPlay, SelectTask, Socket, GetElapsed, DrawGraph, LoadHostSummary, ReloadHostSummaryList, JobIsFinished, SetTaskStyles, DigestEvent,
    UpdateDOM, EventViewer, DeleteJob, PlaybookRun, HostEventsViewer, LoadPlays, LoadTasks, LoadHosts, HostsEdit, ParseVariableString) {

    ClearScope();

    var job_id = $routeParams.id,
        event_socket,
        scope = $scope,
        api_complete = false,
        refresh_count = 0,
        lastEventId = 0,
        verbosity_options,
        job_type_options,
        checkCount = 0;

    scope.plays = [];
    scope.hosts = [];
    scope.tasks = [];
    scope.hostResults = [];

    scope.hostResultsMaxRows = 200;
    scope.hostSummariesMaxRows = 200;
    scope.tasksMaxRows = 200;
    scope.playsMaxRows = 200;

    // Set the following to true when 'Loading...' message desired
    scope.playsLoading = true;
    scope.tasksLoading = true;
    scope.hostResultsLoading = true;
    scope.hostSummariesLoading = true;

    scope.liveEventProcessing = true;     // true while job is active and live events are arriving
    scope.pauseLiveEvents = false;        // control play/pause state of event processing

    scope.job_status = {};
    scope.job_id = job_id;
    scope.auto_scroll = false;

    scope.searchPlaysEnabled = true;
    scope.searchTasksEnabled = true;
    scope.searchHostsEnabled = true;
    scope.searchHostSummaryEnabled = true;
    scope.search_play_status = 'all';
    scope.search_task_status = 'all';
    scope.search_host_status = 'all';
    scope.search_host_summary_status = 'all';

    scope.haltEventQueue = false;
    scope.processing = false;
    scope.lessStatus = true;

    scope.host_summary = {};
    scope.host_summary.ok = 0;
    scope.host_summary.changed = 0;
    scope.host_summary.unreachable = 0;
    scope.host_summary.failed = 0;
    scope.host_summary.total = 0;

    scope.jobData = {};

    verbosity_options = [
        { value: 0, label: 'Default' },
        { value: 1, label: 'Verbose' },
        { value: 3, label: 'Debug' }
    ];

    job_type_options = [
        { value: 'run', label: 'Run' },
        { value: 'check', label: 'Check' }
    ];

    scope.eventsHelpText = "<p><i class=\"fa fa-circle successful-hosts-color\"></i> Successful</p>\n" +
        "<p><i class=\"fa fa-circle changed-hosts-color\"></i> Changed</p>\n" +
        "<p><i class=\"fa fa-circle unreachable-hosts-color\"></i> Unreachable</p>\n" +
        "<p><i class=\"fa fa-circle failed-hosts-color\"></i> Failed</p>\n" +
        "<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>\n";

    function openSocket() {
        event_socket =  Socket({
            scope: scope,
            endpoint: "job_events"
        });
        event_socket.init();
        event_socket.on("job_events-" + job_id, function(data) {
            if (api_complete && data.id > lastEventId) {
                data.event = data.event_name;
                DigestEvent({ scope: scope, event: data });
            }
        });
    }
    openSocket();

    $rootScope.checkSocketConnectionInterval = setInterval(function() {
        if (event_socket.checkStatus() === 'error' || checkCount > 2) {
            // there's an error or we're stuck in a 'connecting' state. attempt to reconnect
            $log.debug('job detail page: initializing and restarting socket connections');
            event_socket = null;
            openSocket();
            checkCount = 0;
        }
        else if (event_socket.checkStatus() === 'connecting') {
            checkCount++;
        }
        else {
            checkCount = 0;
        }
    }, 3000);

    if ($rootScope.removeJobStatusChange) {
        $rootScope.removeJobStatusChange();
    }
    $rootScope.removeJobStatusChange = $rootScope.$on('JobStatusChange', function(e, data) {
        // if we receive a status change event for the current job indicating the job
        // is finished, stop event queue processing and reload
        if (parseInt(data.unified_job_id, 10) === parseInt(job_id,10)) {
            if (data.status === 'failed' || data.status === 'canceled' ||
                    data.status === 'error' || data.status === 'successful') {
                $scope.liveEventProcessing = false;
                if ($rootScope.jobDetailInterval) {
                    window.clearInterval($rootScope.jobDetailInterval);
                }
                if (!scope.pauseLiveEvents) {
                    $scope.$emit('LoadJob'); //this is what is used for the refresh
                }
            }
        }
    });


    if (scope.removeInitialLoadComplete) {
        scope.removeInitialLoadComplete();
    }
    scope.removeInitialLoadComplete = scope.$on('InitialLoadComplete', function() {
        var url;
        Wait('stop');

        if (JobIsFinished(scope)) {
            scope.liveEventProcessing = false; // signal that event processing is over and endless scroll
            scope.pauseLiveEvents = false;      // should be enabled
            url = scope.job.related.job_events + '?event=playbook_on_stats';
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    if (data.results.length > 0) {
                        LoadHostSummary({
                            scope: scope,
                            data: data.results[0].event_data
                        });
                    }
                    UpdateDOM({ scope: scope });
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });

            $log.debug('Job completed!');
            $log.debug(scope.jobData);
        }
        else {
            api_complete = true;  //trigger events to start processing
            if ($rootScope.jobDetailInterval) {
                window.clearInterval($rootScope.jobDetailInterval);
            }
            $rootScope.jobDetailInterval = setInterval(function() {
                UpdateDOM({ scope: scope });
            }, 2000);
        }
    });

    if (scope.removeLoadHostSummaries) {
        scope.removeLoadHostSummaries();
    }
    scope.removeHostSummaries = scope.$on('LoadHostSummaries', function() {
        var url = scope.job.related.job_host_summaries + '?';
        url += '&page_size=' + scope.hostSummariesMaxRows + '&order_by=host_name';

        scope.jobData.hostSummaries = {};

        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                scope.next_host_summaries = data.next;
                data.results.forEach(function(event) {
                    var name;
                    if (event.host_name) {
                        name = event.host_name;
                    }
                    else {
                        name = "<deleted host>";
                    }
                    scope.jobData.hostSummaries[event.id] = {
                        id: event.host,
                        name: name,
                        ok: event.ok,
                        changed: event.changed,
                        unreachable: event.dark,
                        failed: event.failures,
                        status: (event.failed) ? 'failed' : 'successful'
                    };
                });
                scope.$emit('InitialLoadComplete');
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + '. GET returned: ' + status });
            });
    });

    if (scope.removeLoadHosts) {
        scope.removeLoadHosts();
    }
    scope.removeLoadHosts = scope.$on('LoadHosts', function() {
        if (scope.activeTask) {
            var play = scope.jobData.plays[scope.activePlay],
                task = play.tasks[scope.activeTask],
                url;

            url = scope.job.related.job_events + '?parent=' + task.id + '&';
            url += 'event__startswith=runner&page_size=' + scope.hostResultsMaxRows + '&order_by=-host__name';

            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    var idx, event, status, status_text, item, msg;
                    if (data.results.length > 0) {
                        lastEventId =  data.results[0].id;
                    }
                    scope.next_host_results = data.next;
                    for (idx=data.results.length - 1; idx >= 0; idx--) {
                        event = data.results[idx];
                        if (event.event === "runner_on_skipped") {
                            status = 'skipped';
                        }
                        else if (event.event === "runner_on_unreachable") {
                            status = 'unreachable';
                        }
                        else {
                            status = (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful';
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

                        if (event.event_data && event.event_data.res) {
                            item = event.event_data.res.item;
                            if (typeof item === "object") {
                                item = JSON.stringify(item);
                            }
                        }

                        msg = '';
                        if (event.event_data && event.event_data.res) {
                            if (typeof event.event_data.res === 'object') {
                                msg = event.event_data.res.msg;
                            } else {
                                msg = event.event_data.res;
                            }
                        }

                        if (event.event !== "runner_on_no_hosts") {
                            task.hostResults[event.id] = {
                                id: event.id,
                                status: status,
                                status_text: status_text,
                                host_id: event.host,
                                task_id: event.parent,
                                name: event.event_data.host,
                                created: event.created,
                                msg: msg,
                                item: item
                            };
                        }
                    }
                    scope.$emit('LoadHostSummaries');
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
        else {
            scope.$emit('LoadHostSummaries');
        }
    });

    if (scope.removeLoadTasks) {
        scope.removeLoadTasks();
    }
    scope.removeLoadTasks = scope.$on('LoadTasks', function() {
        if (scope.activePlay) {
            var play = scope.jobData.plays[scope.activePlay], url;

            url = scope.job.url + 'job_tasks/?event_id=' + play.id;
            url += '&page_size=' + scope.tasksMaxRows + '&order_by=id';

            Rest.setUrl(url);
            Rest.get()
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

                        if (idx < data.length - 1) {
                            // end date = starting date of the next event
                            end = data[idx + 1].created;
                        }
                        else {
                            // no next event (task), get the end time of the play
                            end = scope.jobData.plays[scope.activePlay].finished;
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
                        if (play.tasks[event.id].hostCount === 0) {
                            play.tasks[event.id].status_text = 'No matching hosts';
                            play.tasks[event.id].status_tip = "Event ID: " + event.id + "<br />Status: No matching hosts";
                        }
                        play.taskCount++;
                        SetTaskStyles({
                            task: play.tasks[event.id]
                        });
                    });
                    if (scope.activeTask && scope.jobData.plays[scope.activePlay] && scope.jobData.plays[scope.activePlay].tasks[scope.activeTask]) {
                        scope.jobData.plays[scope.activePlay].tasks[scope.activeTask].taskActiveClass = 'active';
                    }
                    scope.$emit('LoadHosts');
                })
                .error(function(data) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
        else {
            scope.$emit('LoadHostSummaries');
        }
    });

    if (scope.removeLoadPlays) {
        scope.removeLoadPlays();
    }
    scope.removeLoadPlays = scope.$on('LoadPlays', function(e, events_url) {

        scope.host_summary.ok = 0;
        scope.host_summary.changed = 0;
        scope.host_summary.unreachable = 0;
        scope.host_summary.failed = 0;
        scope.host_summary.total = 0;

        scope.jobData.plays = {};

        var url = scope.job.url  + 'job_plays/?order_by=id';
        url += '&page_size=' + scope.playsMaxRows + '&order_by=id';

        Rest.setUrl(url);
        Rest.get()
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
                    if (scope.job_status.status === 'failed' || scope.job_status.status === 'error' &&
                        (!scope.job_status.explanation)) {
                        scope.job_status.explanation = "<a href=\"/#/jobs/" + scope.job_id + "/stdout\" target=\"_blank\">View stdout for more detail <i class=\"fa fa-external-link\"></i></a>";
                    }
                }
                data.results.forEach(function(event, idx) {
                    var status, status_text, start, end, elapsed, ok, changed, failed, skipped;

                    status = (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful';
                    status_text = (event.failed) ? 'Failed' : (event.changed) ? 'Changed' : 'OK';
                    start = event.started;

                    if (idx < data.length - 1) {
                        // end date = starting date of the next event
                        end = data[idx + 1].started;
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
                        scope.jobData.plays[event.id].status_text = 'No matching hosts';
                        scope.jobData.plays[event.id].status_tip = "Event ID: " + event.id + "<br />Status: No matching hosts";
                    }

                    scope.host_summary.ok += ok;
                    scope.host_summary.changed += changed;
                    scope.host_summary.unreachable += (event.unreachable_count) ? event.unreachable_count : 0;
                    scope.host_summary.failed += failed;
                    scope.host_summary.total = scope.host_summary.ok + scope.host_summary.changed + scope.host_summary.unreachable +
                        scope.host_summary.failed;
                });
                if (scope.activePlay && scope.jobData.plays[scope.activePlay]) {
                    scope.jobData.plays[scope.activePlay].playActiveClass = 'active';
                }
                scope.$emit('LoadTasks', events_url);
            })
            .error( function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + '. GET returned: ' + status });
            });
    });


    if (scope.removeGetCredentialNames) {
        scope.removeGetCredentialNames();
    }
    scope.removeGetCredentialNames = scope.$on('GetCredentialNames', function(e, data) {
        var url;
        if (data.credential) {
            url = GetBasePath('credentials') + data.credential + '/';
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    scope.credential_name = data.name;
                })
                .error( function(data, status) {
                    scope.credential_name = '';
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
        if (data.cloud_credential) {
            url = GetBasePath('credentials') + data.cloud_credential + '/';
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    scope.cloud_credential_name = data.name;
                })
                .error( function(data, status) {
                    scope.credential_name = '';
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
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
        scope.LoadHostSummaries = true;

        // Load the job record
        Rest.setUrl(GetBasePath('jobs') + job_id + '/');
        Rest.get()
            .success(function(data) {
                var i;
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

                if (data.status === 'successful' || data.status === 'failed' || data.status === 'error' || data.status === 'canceled') {
                    scope.job_status.finished = data.finsished;
                    scope.liveEventProcessing = false;
                    scope.pauseLiveEvents = false;
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
                //scope.setSearchAll('host');
                scope.$emit('LoadPlays', data.related.job_events);
                if (!scope.credential_name) {
                    scope.$emit('GetCredentialNames', data);
                }
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to retrieve job: ' + $routeParams.id + '. GET returned: ' + status });
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
        else {
            // Check if the graph needs to redraw
            setTimeout(function() { DrawGraph({ scope: scope, resize: true }); }, 500);
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
            $('#job-detail-container').css({ "width": "58.33333333%", "padding-right": "7px" });
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

        scope.lessStatus = true; // close the view more status option

        // Detail table height adjusting. First, put page height back to 'normal'.
        $('#plays-table-detail').height(80);
        //$('#plays-table-detail').mCustomScrollbar("update");
        $('#tasks-table-detail').height(120);
        //$('#tasks-table-detail').mCustomScrollbar("update");
        $('#hosts-table-detail').height(150);
        //$('#hosts-table-detail').mCustomScrollbar("update");
        height = $(window).height() - $('#main-menu-container .navbar').outerHeight() - $('#breadcrumb-container').outerHeight() -
            $('#job-detail-container').outerHeight() - $('#job-detail-footer').outerHeight() - 20;
        if (height > 15) {
            // there's a bunch of white space at the bottom, let's use it
            $('#plays-table-detail').height(80 + (height * 0.10));
            $('#tasks-table-detail').height(120 + (height * 0.20));
            $('#hosts-table-detail').height(150 + (height * 0.70));
        }
        // Summary table height adjusting.
        height = ($('#job-detail-container').height() / 2) - $('#hosts-summary-section .header').outerHeight() -
            $('#hosts-summary-section .table-header').outerHeight() -
            $('#summary-search-section').outerHeight() - 20;
        $('#hosts-summary-table').height(height);
        //$('#hosts-summary-table').mCustomScrollbar("update");
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

    scope.toggleSummary = function(hide) {
        var docw, doch, height = $('#job-detail-container').height(), slide_width;
        if (!hide) {
            docw = $(window).width();
            doch = $(window).height();
            slide_width = (docw < 840) ? '100%' : '80%';
            $('#summary-button').hide();
            $('.overlay').css({
                width: $(document).width(),
                height: $(document).height()
            }).show();

            // Adjust the summary table height
            $('#job-summary-container .job_well').height(height - 18).css({
                'box-shadow': '-3px 3px 5px 0 #ccc'
            });
            height = Math.floor($('#job-detail-container').height() * 0.5) -
                $('#hosts-summary-section .header').outerHeight() -
                $('#hosts-summary-section .table-header').outerHeight() -
                $('#hide-summary-button').outerHeight() -
                $('#summary-search-section').outerHeight() -
                $('#hosts-summary-section .header').outerHeight() -
                $('#hosts-summary-section .legend').outerHeight();
            $('#hosts-summary-table').height(height - 50);
            //$('#hosts-summary-table').mCustomScrollbar("update");

            $('#hide-summary-button').show();

            $('#job-summary-container').css({
                top: 0,
                right: 0,
                width: slide_width,
                'z-index': 1090,
                'padding-right': '15px',
                'padding-left': '15px'
            }).show('slide', {'direction': 'right'});

            setTimeout(function() { DrawGraph({ scope: scope, resize: true }); }, 500);
        }
        else {
            $('.overlay').hide();
            $('#summary-button').show();
            $('#job-summary-container').hide('slide', {'direction': 'right'});
        }
    };

    scope.objectIsEmpty = function(obj) {
        if (angular.isObject(obj)) {
            return (Object.keys(obj).length > 0) ? false : true;
        }
        return true;
    };

    scope.toggleLessStatus = function() {
        if (!scope.lessStatus) {
            $('#job-status-form .toggle-show').hide(400);
            scope.lessStatus = true;
        }
        else {
            $('#job-status-form .toggle-show').show(400);
            scope.lessStatus = false;
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
        if (scope.search_task_name) {
            scope.searchTasksEnabled = false;
        }
        else {
            scope.searchTasksEnabled = true;
        }
        if (!scope.liveEventProcessing || scope.pauseLiveEvents) {
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
        if (scope.search_host_name) {
            scope.searchHostsEnabled = false;
        }
        else {
            scope.searchHostsEnabled = true;
        }
        if (!scope.liveEventProcessing || scope.pauseLiveEvents) {
            LoadHosts({
                scope: scope
            });
        }
    };

    scope.searchHostsKeyPress = function(e) {
        if (e.keyCode === 13) {
            scope.searchHosts();
            e.stopPropagation();
        }
    };

    scope.searchHostSummary = function() {
        if (scope.search_host_summary_name) {
            scope.searchHostSummaryEnabled = false;
        }
        else {
            scope.searchHostSummaryEnabled = true;
        }
        if (!scope.liveEventProcessing || scope.pauseLiveEvents) {
            ReloadHostSummaryList({
                scope: scope
            });
        }
    };

    scope.searchHostSummaryKeyPress = function(e) {
        if (e.keyCode === 13) {
            scope.searchHostSummary();
            e.stopPropagation();
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

    scope.filterHostStatus = function() {
        scope.search_host_status = (scope.search_host_status === 'all') ? 'failed' : 'all';
        if (!scope.liveEventProcessing || scope.pauseLiveEvents) {
            LoadHosts({
                scope: scope
            });
        }
    };

    scope.filterHostSummaryStatus = function() {
        scope.search_host_summary_status = (scope.search_host_summary_status === 'all') ? 'failed' : 'all';
        if (!scope.liveEventProcessing || scope.pauseLiveEvents) {
            ReloadHostSummaryList({
                scope: scope
            });
        }
    };

    scope.viewHostResults = function(id) {
        EventViewer({
            scope: scope,
            url: scope.job.related.job_events,
            parent_id: scope.selectedTask,
            event_id: id,
            title: 'Host Events'
        });
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
        PlaybookRun({
            scope: scope,
            id: scope.job.id
        });
    };

    scope.playsScrollDown = function() {
        // check for more plays when user scrolls to bottom of play list...
        if (((!scope.liveEventProcessing) || (scope.liveEventProcessing && scope.pauseLiveEvents)) && scope.next_plays) {
            $('#playsMoreRows').fadeIn();
            scope.playsLoading = true;
            Rest.setUrl(scope.next_plays);
            Rest.get()
                .success( function(data) {
                    scope.next_plays = data.next;
                    data.results.forEach(function(event, idx) {
                        var status, status_text, start, end, elapsed, ok, changed, failed, skipped;

                        status = (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful';
                        status_text = (event.failed) ? 'Failed' : (event.changed) ? 'Changed' : 'OK';
                        start = event.started;

                        if (idx < data.length - 1) {
                            // end date = starting date of the next event
                            end = data[idx + 1].started;
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
            Rest.setUrl(scope.next_tasks);
            Rest.get()
                .success(function(data) {
                    scope.next_tasks = data.next;
                    data.results.forEach(function(event, idx) {
                        var end, elapsed, status, status_text;
                        if (idx < data.length - 1) {
                            // end date = starting date of the next event
                            end = data[idx + 1].created;
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
            Rest.setUrl(scope.next_host_results);
            Rest.get()
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

    scope.hostSummariesScrollDown = function() {
        // check for more hosts when user scrolls to bottom of host summaries list...
        if (((!scope.liveEventProcessing) || (scope.liveEventProcessing && scope.pauseLiveEvents)) && scope.next_host_summaries) {
            scope.hostSummariesLoading = true;
            Rest.setUrl(scope.next_host_summaries);
            Rest.get()
                .success(function(data) {
                    scope.next_host_summaries = data.next;
                    data.results.forEach(function(row) {
                        var name;
                        if (event.host_name) {
                            name = event.host_name;
                        }
                        else {
                            name = "<deleted host>";
                        }
                        scope.hosts.push({
                            id: row.host,
                            name: name,
                            ok: row.ok,
                            changed: row.changed,
                            unreachable: row.dark,
                            failed: row.failures
                        });
                    });
                    $('#hostSummariesMoreRows').fadeOut();
                    scope.hostSummariesLoading = false;
                })
                .error(function(data, status) {
                    $('#hostSummariesMoreRows').fadeOut();
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + scope.next_host_summaries + '. GET returned: ' + status });
                });
        }
    };

    scope.hostEventsViewer = function(id, name, status) {
        HostEventsViewer({
            scope: scope,
            id: id,
            name: name,
            url: scope.job.related.job_events,
            job_id: scope.job.id,
            status: status
        });
    };
    scope.refresh = function(){
        $scope.$emit('LoadJob');
    };

    scope.editHost = function(id) {
        HostsEdit({
            host_scope: scope,
            group_scope: null,
            host_id: id,
            inventory_id: scope.job.inventory,
            mode: 'edit',  // 'add' or 'edit'
            selected_group_id: null
        });
    };
}

JobDetailController.$inject = [ '$location', '$rootScope', '$scope', '$compile', '$routeParams', '$log', 'ClearScope', 'Breadcrumbs', 'LoadBreadCrumbs', 'GetBasePath',
    'Wait', 'Rest', 'ProcessErrors', 'SelectPlay', 'SelectTask', 'Socket', 'GetElapsed', 'DrawGraph', 'LoadHostSummary', 'ReloadHostSummaryList',
    'JobIsFinished', 'SetTaskStyles', 'DigestEvent', 'UpdateDOM', 'EventViewer', 'DeleteJob', 'PlaybookRun', 'HostEventsViewer', 'LoadPlays', 'LoadTasks',
    'LoadHosts', 'HostsEdit', 'ParseVariableString'
];
