/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobDetail.js
 *
 */

'use strict';

function JobDetailController ($rootScope, $scope, $compile, $routeParams, $log, ClearScope, Breadcrumbs, LoadBreadCrumbs, GetBasePath, Wait, Rest,
    ProcessErrors, SelectPlay, SelectTask, Socket, GetElapsed, FilterAllByHostName, DrawGraph, LoadHostSummary, ReloadHostSummaryList,
    JobIsFinished, SetTaskStyles, DigestEvent, UpdateDOM) {

    ClearScope();

    var job_id = $routeParams.id,
        event_socket,
        scope = $scope,
        api_complete = false,
        refresh_count = 0,
        lastEventId = 0;

    scope.plays = [];
    scope.hosts = [];
    scope.tasks = [];
    scope.hostResults = [];

    scope.hostResultsMaxRows = 15;
    scope.hostSummariesMaxRows = 15;
    scope.tasksMaxRows = 15;
    scope.playsMaxRows = 15;

    scope.liveEventProcessing = true;  // control play/pause state of event processing

    scope.search_all_tasks = [];
    scope.search_all_plays = [];
    scope.job_status = {};
    scope.job_id = job_id;
    scope.auto_scroll = false;
    scope.searchTaskHostsEnabled = true;
    scope.searchSummaryHostsEnabled = true;
    scope.searchAllHostsEnabled = true;
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

    scope.eventsHelpText = "<p><i class=\"fa fa-circle successful-hosts-color\"></i> Successful</p>\n" +
        "<p><i class=\"fa fa-circle changed-hosts-color\"></i> Changed</p>\n" +
        "<p><i class=\"fa fa-circle unreachable-hosts-color\"></i> Unreachable</p>\n" +
        "<p><i class=\"fa fa-circle failed-hosts-color\"></i> Failed</p>\n" +
        "<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>\n";

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


    if ($rootScope.removeJobStatusChange) {
        $rootScope.removeJobStatusChange();
    }
    $rootScope.removeJobStatusChange = $rootScope.$on('JobStatusChange', function(e, data) {
        // if we receive a status change event for the current job indicating the job
        // is finished, stop event queue processing and reload
        if (parseInt(data.unified_job_id, 10) === parseInt(job_id,10)) {
            if (data.status === 'failed' || data.status === 'canceled' ||
                    data.status === 'error' || data.status === 'successful') {
                if ($rootScope.jobDetailInterval) {
                    window.clearInterval($rootScope.jobDetailInterval);
                }
                $scope.$emit('LoadJob');
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
            $scope.liveEventProcessing = false; // signal that event processing is over and endless scroll
                                                // should be enabled
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
            $rootScope.jobDetailInterval = setInterval(function() {
                $log.debug('Updating the DOM...');
                UpdateDOM({ scope: scope });
            }, 5000);
        }
    });

    if (scope.removeLoadHostSummaries) {
        scope.removeLoadHostSummaries();
    }
    scope.removeHostSummaries = scope.$on('LoadHostSummaries', function() {
        var url = scope.job.related.job_host_summaries + '?';
        url += '&page_size=' + scope.hostSummariesMaxRows + '&order_by=host__name';

        scope.jobData.hostSummaries = {};

        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                data.results.forEach(function(event) {
                    scope.jobData.hostSummaries[event.id] = {
                        id: event.host,
                        name: event.summary_fields.host.name,
                        ok: event.ok,
                        changed: event.changed,
                        unreachable: event.dark,
                        failed: event.failures
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
            url += 'host__isnull=false&page_size=' + scope.hostResultsMaxRows + '&order_by=-host__name';
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    var idx, event;
                    if (data.results.length > 0) {
                        lastEventId =  data.results[0].id;
                    }
                    for (idx=data.results.length - 1; idx >= 0; idx--) {
                        event = data.results[idx];
                        task.hostResults[event.id] = {
                            id: event.id,
                            status: ( (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful' ),
                            host_id: event.host,
                            task_id: event.parent,
                            name: event.event_data.host,
                            created: event.created,
                            msg: ( (event.event_data && event.event_data.res) ? event.event_data.res.msg : '' )
                        };
                    }
                    scope.$emit('LoadHostSummaries');
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
        else {
            scope.jobData.hostSummaries = {};
            scope.$emit('InitialLoadComplete');
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
                    if (data.results.length > 0) {
                        lastEventId = data.results[data.results.length - 1].id;
                        scope.activeTask = data.results[0].id;
                    }
                    data.results.forEach(function(event, idx) {
                        var end, elapsed;

                        if (!play.firstTask) {
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

                        play.tasks[event.id] = {
                            id: event.id,
                            play_id: scope.activePlay,
                            name: event.name,
                            status: ( (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful' ),
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
                            taskActiveClass: '',
                            hostResults: {}
                        };
                        SetTaskStyles({
                            task: play.tasks[event.id]
                        });
                    });
                    if (scope.activeTask) {
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
            scope.jobData.hostSummaries = {};
            scope.$emit('InitialLoadComplete');
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
                if (data.results.length > 0) {
                    lastEventId = data.results[data.results.length - 1].id;
                    scope.activePlay = data.results[0].id;
                }
                data.results.forEach(function(event, idx) {
                    var status, start, end, elapsed;

                    status = (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful';
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
                        elapsed: elapsed,
                        hostCount: 0,
                        fistTask: null,
                        playActiveClass: '',
                        tasks: {}
                    };

                    scope.host_summary.ok += (data.ok_count) ? data.ok_count : 0;
                    scope.host_summary.changed += (data.changed_count) ? data.changed_count : 0;
                    scope.host_summary.unreachable += (data.unreachable_count) ? data.unreachable_count : 0;
                    scope.host_summary.failed += (data.failed_count) ? data.failed_count : 0;
                    scope.host_summary.total = scope.host_summary.ok + scope.host_summary.changed +
                        scope.host_summary.unreachable + scope.host_summary.failed;
                });
                if (scope.activePlay) {
                    scope.jobData.plays[scope.activePlay].playActiveClass = 'active';
                }
                scope.$emit('LoadTasks', events_url);
                //scope.$emit('FixPlaysScroll');
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
            url = GetBasePath('credentials') + data.credential + '/';
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
        // Load the job record
        Rest.setUrl(GetBasePath('jobs') + job_id + '/');
        Rest.get()
            .success(function(data) {
                scope.job = data;
                scope.job_template_name = data.name;
                scope.project_name = (data.summary_fields.project) ? data.summary_fields.project.name : '';
                scope.inventory_name = (data.summary_fields.inventory) ? data.summary_fields.inventory.name : '';
                scope.job_template_url = '/#/job_templates/' + data.unified_job_template;
                scope.inventory_url = (scope.inventory_name && data.inventory) ? '/#/inventories/' + data.inventory : '';
                scope.project_url = (scope.project_name && data.project) ? '/#/projects/' + data.project : '';
                scope.job_type = data.job_type;
                scope.playbook = data.playbook;
                scope.credential = data.credential;
                scope.cloud_credential = data.cloud_credential;
                scope.forks = data.forks;
                scope.limit = data.limit;
                scope.verbosity = data.verbosity;
                scope.job_tags = data.job_tags;

                // In the case the job is already completed, or an error already happened,
                // populate scope.job_status info
                scope.job_status.status = (data.status === 'waiting' || data.status === 'new') ? 'pending' : data.status;
                scope.job_status.started = data.started;
                scope.job_status.status_class = ((data.status === 'error' || data.status === 'failed') && data.job_explanation) ? "alert alert-danger" : "";
                scope.job_status.finished = data.finished;
                scope.job_status.explanation = data.job_explanation;

                if (data.started && data.finished) {
                    scope.job_status.elapsed = GetElapsed({
                        start: data.started,
                        end: data.finished
                    });
                }
                else {
                    scope.job_status.elapsed = '00:00:00';
                }
                scope.setSearchAll('host');
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

    if (scope.removeFixPlaysScroll) {
        scope.removeFixPlaysScroll();
    }
    scope.removeFixPlaysScroll = scope.$on('FixPlaysScroll', function() {
        $('#plays-table-detail').mCustomScrollbar("update");
        setTimeout( function() {
            $('#plays-table-detail').mCustomScrollbar("scrollTo", "bottom");
        }, 500);
    });

    if (scope.removeFixTasksScroll) {
        scope.removeFixTasksScroll();
    }
    scope.removeFixTasksScroll = scope.$on('FixTasksScroll', function() {
        $('#tasks-table-detail').mCustomScrollbar("update");
        setTimeout( function() {
            $('#tasks-table-detail').mCustomScrollbar("scrollTo", "bottom");
        }, 500);
    });

    if (scope.removeFixHostResultsScroll) {
        scope.removeFixHostResultsScroll();
    }
    scope.removeFixHostResultsScroll = scope.$on('FixHostResultsScroll', function() {
        $('#hosts-table-detail').mCustomScrollbar("update");
        setTimeout( function() {
            $('#hosts-table-detail').mCustomScrollbar("scrollTo", "bottom");
        }, 500);
    });

    scope.adjustSize = function() {
        var height, ww = $(window).width();
        if (ww < 1240) {
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
        // Detail table height adjusting. First, put page height back to 'normal'.
        $('#plays-table-detail').height(150);
        $('#plays-table-detail').mCustomScrollbar("update");
        $('#tasks-table-detail').height(150);
        $('#tasks-table-detail').mCustomScrollbar("update");
        $('#hosts-table-detail').height(150);
        $('#hosts-table-detail').mCustomScrollbar("update");
        //height = $('#wrap').height() - $('.site-footer').outerHeight() - $('.main-container').height();
        height = $(window).height() - $('#main-menu-container .navbar').outerHeight()
        if (height > 15) {
            // there's a bunch of white space at the bottom, let's use it
            $('#plays-table-detail').height(150 + (height / 3));
            $('#plays-table-detail').mCustomScrollbar("update");
            $('#tasks-table-detail').height(150 + (height / 3));
            $('#tasks-table-detail').mCustomScrollbar("update");
            $('#hosts-table-detail').height(150 + (height / 3));
            $('#hosts-table-detail').mCustomScrollbar("update");
        }
        // Summary table height adjusting.
        height = ($('#job-detail-container').height() / 2) - $('#hosts-summary-section .header').outerHeight() -
            $('#hosts-summary-section .table-header').outerHeight() -
            $('#summary-search-section').outerHeight() - 20;
        $('#hosts-summary-table').height(height);
        $('#hosts-summary-table').mCustomScrollbar("update");
        scope.$emit('RefreshCompleted');
    };

    setTimeout(function() { scope.adjustSize(); }, 500);

    // Use debounce for the underscore library to adjust after user resizes window.
    $(window).resize(_.debounce(function(){
        scope.adjustSize();
    }, 500));

    scope.setSearchAll = function(search) {
        if (search === 'host') {
            scope.search_all_label = 'Host';
            scope.searchAllDisabled = false;
            scope.search_all_placeholder = 'Search all by host name';
        }
        else {
            scope.search_all_label = 'Failures';
            scope.search_all_placeholder = 'Show failed events';
            scope.searchAllDisabled = true;
            scope.search_all_placeholder = '';
        }
    };

    scope.selectPlay = function(id) {
        scope.auto_scroll_plays = false;
        SelectPlay({
            scope: scope,
            id: id
        });
    };

    scope.selectTask = function(id) {
        scope.auto_scroll_tasks = false;
        SelectTask({
            scope: scope,
            id: id
        });
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
            $('#hosts-summary-table').mCustomScrollbar("update");

            $('#hide-summary-button').show();

            $('#job-summary-container').css({
                top: 0,
                right: 0,
                width: slide_width,
                'z-index': 2000,
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
        scope.lessStatus = (scope.lessStatus) ? false : true;
    };

    scope.HostDetailOnTotalScroll = _.debounce(function() {
        // Called when user scrolls down (or forward in time)
        var url, mcs = arguments[0];
        scope.$apply(function() {
            if ((!scope.liveEventProcessing) && scope.activeTask && scope.hostResults.length) {
                scope.auto_scroll = true;
                url = GetBasePath('jobs') + job_id + '/job_events/?parent=' + scope.activeTask + '&';
                url += (scope.search_all_hosts_name) ? 'host__name__icontains=' + scope.search_all_hosts_name + '&' : '';
                url += (scope.searchAllStatus === 'failed') ? 'failed=true&' : '';
                url += 'host__name__gt=' + scope.hostResults[scope.hostResults.length - 1].name + '&host__isnull=false&page_size=' + scope.hostResultsMaxRows + '&order_by=host__name';
                Wait('start');
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data) {
                        data.results.forEach(function(row) {
                            scope.hostResults.push({
                                id: row.id,
                                status: ( (row.failed) ? 'failed': (row.changed) ? 'changed' : 'successful' ),
                                host_id: row.host,
                                task_id: row.parent,
                                name: row.event_data.host,
                                created: row.created,
                                msg: ( (row.event_data && row.event_data.res) ? row.event_data.res.msg : '' )
                            });
                            if (scope.hostResults.length > scope.hostResultsMaxRows) {
                                scope.hostResults.shift();
                            }
                        });
                        if (data.next) {
                            // there are more rows. move dragger up, letting user know.
                            setTimeout(function() { $('#hosts-table-detail .mCSB_dragger').css({ top: (mcs.draggerTop - 15) + 'px'}); }, 700);
                        }
                        scope.auto_scroll = false;
                        //rebuildHostResultsMap();
                        Wait('stop');
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                    });
            }
        });
    }, 300);

    scope.HostDetailOnTotalScrollBack = _.debounce(function() {
        // Called when user scrolls up (or back in time)
        var url, mcs = arguments[0];
        scope.$apply(function() {
            if ((!scope.liveEventProcessing) && scope.activeTask && scope.hostResults.length) {
                scope.auto_scroll = true;
                url = GetBasePath('jobs') + job_id + '/job_events/?parent=' + scope.activeTask + '&';
                url += (scope.search_all_hosts_name) ? 'host__name__icontains=' + scope.search_all_hosts_name + '&' : '';
                url += (scope.searchAllStatus === 'failed') ? 'failed=true&' : '';
                url += 'host__name__lt=' + scope.hostResults[0].name + '&host__isnull=false&page_size=' + scope.hostResultsMaxRows + '&order_by=-host__name';
                Wait('start');
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data) {
                        data.results.forEach(function(row) {
                            scope.hostResults.unshift({
                                id: row.id,
                                status: ( (row.failed) ? 'failed': (row.changed) ? 'changed' : 'successful' ),
                                host_id: row.host,
                                task_id: row.parent,
                                name: row.event_data.host,
                                created: row.created,
                                msg: ( (row.event_data && row.event_data.res) ? row.event_data.res.msg : '' )
                            });
                            if (scope.hostResults.length > scope.hostResultsMaxRows) {
                                scope.hostResults.pop();
                            }
                        });
                        if (data.next) {
                            // there are more rows. move dragger down, letting user know.
                            setTimeout(function() { $('#hosts-table-detail .mCSB_dragger').css({ top: (mcs.draggerTop + 15) + 'px' }); }, 700);
                        }
                        //rebuildHostResultsMap();
                        Wait('stop');
                        scope.auto_scroll = false;
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                    });
            }
        });
    }, 300);


    scope.TasksOnTotalScroll = _.debounce(function() {
        // Called when user scrolls down (or forward in time)
        var url, mcs = arguments[0];
        scope.$apply(function() {
            if ((!scope.liveEventProcessing) && scope.activePlay && scope.tasks.length) {
                scope.auto_scroll = true;
                url = scope.job.url + 'job_tasks/?event_id=' + scope.activePlay;
                url += (scope.search_all_tasks.length > 0) ? '&id__in=' + scope.search_all_tasks.join() : '';
                url += (scope.searchAllStatus === 'failed') ? '&failed=true' : '';
                url += '&id__gt=' + scope.tasks[scope.tasks.length - 1].id + '&page_size=' + scope.tasksMaxRows + '&order_by=id';
                Wait('start');
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data) {
                        data.results.forEach(function(event, idx) {
                            var end, elapsed;
                            if (idx < data.length - 1) {
                                // end date = starting date of the next event
                                end = data[idx + 1].created;
                            }
                            else {
                                // no next event (task), get the end time of the play
                                scope.plays.every(function(p, j) {
                                    if (p.id === scope.activePlay) {
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
                            scope.tasks.push({
                                id: event.id,
                                play_id: scope.activePlay,
                                name: event.name,
                                status: ( (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful' ),
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
                            if (scope.tasks.length > scope.tasksMaxRows) {
                                scope.tasks.shift();
                            }
                        });
                        if (data.next) {
                            // there are more rows. move dragger up, letting user know.
                            setTimeout(function() { $('#tasks-table-detail .mCSB_dragger').css({ top: (mcs.draggerTop - 15) + 'px'}); }, 700);
                        }
                        scope.auto_scroll = false;
                        //rebuildTasksMap();
                        Wait('stop');
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                    });
            }
            else {
                scope.auto_scroll_tasks = false;
            }
        });
    }, 300);

    scope.TasksOnTotalScrollBack = _.debounce(function() {
        // Called when user scrolls up (or back in time)
        var url, mcs = arguments[0];
        scope.$apply(function() {
            if ((!scope.liveEventProcessing) && scope.activePlay && scope.tasks.length) {
                scope.auto_scroll = true;
                url = scope.job.url + 'job_tasks/?event_id=' + scope.activePlay;
                url += (scope.search_all_tasks.length > 0) ? '&id__in=' + scope.search_all_tasks.join() : '';
                url += (scope.searchAllStatus === 'failed') ? '&failed=true' : '';
                url += '&id__lt=' + scope.tasks[0].id + '&page_size=' + scope.tasksMaxRows + '&order_by=-id';
                Wait('start');
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data) {
                        data.results.forEach(function(event, idx) {
                            var end, elapsed;
                            if (idx < data.length - 1) {
                                // end date = starting date of the next event
                                end = data[idx + 1].created;
                            }
                            else {
                                // no next event (task), get the end time of the play
                                scope.plays.every(function(p, j) {
                                    if (p.id === scope.activePlay) {
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
                            scope.tasks.unshift({
                                id: event.id,
                                play_id: scope.activePlay,
                                name: event.name,
                                status: ( (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful' ),
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
                                task: scope.tasks[0]
                            });
                            if (scope.tasks.length > scope.tasksMaxRows) {
                                scope.tasks.pop();
                            }
                        });
                        if (data.next) {
                            // there are more rows. move dragger up, letting user know.
                            setTimeout(function() { $('#tasks-table-detail .mCSB_dragger').css({ top: (mcs.draggerTop + 15) + 'px'}); }, 700);
                        }
                        scope.auto_scroll = false;
                        //rebuildTasksMap();
                        Wait('stop');
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                    });
            }
        });
    }, 300);

    scope.HostSummaryOnTotalScroll = function(mcs) {
        var url;
        if ((!scope.liveEventProcessing) && scope.hosts) {
            url = GetBasePath('jobs') + job_id + '/job_host_summaries/?';
            url += (scope.search_all_hosts_name) ? 'host__name__icontains=' + scope.search_all_hosts_name + '&' : '';
            url += (scope.searchAllStatus === 'failed') ? 'failed=true&' : '';
            url += 'host__name__gt=' + scope.hosts[scope.hosts.length - 1].name + '&page_size=' + scope.hostSummariesMaxRows + '&order_by=host__name';
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    setTimeout(function() {
                        scope.$apply(function() {
                            data.results.forEach(function(row) {
                                scope.hosts.push({
                                    id: row.host,
                                    name: row.summary_fields.host.name,
                                    ok: row.ok,
                                    changed: row.changed,
                                    unreachable: row.dark,
                                    failed: row.failures
                                });
                                if (scope.hosts.length > scope.hostSummariesMaxRows) {
                                    scope.hosts.shift();
                                }
                            });
                            if (data.next) {
                                // there are more rows. move dragger up, letting user know.
                                setTimeout(function() { $('#hosts-summary-table .mCSB_dragger').css({ top: (mcs.draggerTop - 15) + 'px'}); }, 700);
                            }
                        });
                    }, 100);
                    Wait('stop');
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
    };

    scope.HostSummaryOnTotalScrollBack = function(mcs) {
        var url;
        if ((!scope.liveEventProcessing) && scope.hosts) {
            url = GetBasePath('jobs') + job_id + '/job_host_summaries/?';
            url += (scope.search_all_hosts_name) ? 'host__name__icontains=' + scope.search_all_hosts_name + '&' : '';
            url += (scope.searchAllStatus === 'failed') ? 'failed=true&' : '';
            url += 'host__name__lt=' + scope.hosts[0].name + '&page_size=' + scope.hostSummariesMaxRows + '&order_by=-host__name';
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    setTimeout(function() {
                        scope.$apply(function() {
                            data.results.forEach(function(row) {
                                scope.hosts.unshift({
                                    id: row.host,
                                    name: row.summary_fields.host.name,
                                    ok: row.ok,
                                    changed: row.changed,
                                    unreachable: row.dark,
                                    failed: row.failures
                                });
                                if (scope.hosts.length > scope.hostSummariesMaxRows) {
                                    scope.hosts.pop();
                                }
                            });
                            if (data.next) {
                                // there are more rows. move dragger down, letting user know.
                                setTimeout(function() { $('#hosts-summary-table .mCSB_dragger').css({ top: (mcs.draggerTop + 15) + 'px' }); }, 700);
                            }
                        });
                    }, 100);
                    Wait('stop');
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
    };

    scope.searchAllByHost = function() {
        if (scope.search_all_hosts_name) {
            FilterAllByHostName({
                scope: scope,
                host: scope.search_all_hosts_name
            });
            scope.searchAllHostsEnabled = false;
        }
        else {
            scope.search_all_tasks = [];
            scope.search_all_plays = [];
            scope.searchAllHostsEnabled = true;
            SelectPlay({
                scope: scope,
                id: (scope.plays.length > 0) ? scope.plays[0].id : null
            });

        }
        ReloadHostSummaryList({
            scope: scope
        });
    };

    scope.allHostNameKeyPress = function(e) {
        if (e.keyCode === 13) {
            scope.searchAllByHost();
        }
    };

    scope.filterByStatus = function(choice) {
        var nxtPlay;
        if (choice === 'Failed') {
            scope.searchAllStatus = 'failed';
            nxtPlay = null;
            scope.plays.every(function(play) {
                if (play.status === 'failed') {
                    nxtPlay = play.id;
                    return false;
                }
                return true;
            });
        }
        else {
            scope.searchAllStatus = '';
            nxtPlay = (scope.plays.length > 0) ? scope.plays[0].id : null;
        }
        SelectPlay({
            scope: scope,
            id: nxtPlay
        });
        ReloadHostSummaryList({
            scope: scope
        });
    };

    scope.viewEvent = function(event_id) {
        $log.debug(event_id);
    };

}

JobDetailController.$inject = [ '$rootScope', '$scope', '$compile', '$routeParams', '$log', 'ClearScope', 'Breadcrumbs', 'LoadBreadCrumbs', 'GetBasePath',
    'Wait', 'Rest', 'ProcessErrors', 'SelectPlay', 'SelectTask', 'Socket', 'GetElapsed', 'FilterAllByHostName', 'DrawGraph',
    'LoadHostSummary', 'ReloadHostSummaryList', 'JobIsFinished', 'SetTaskStyles', 'DigestEvent', 'UpdateDOM'
];
