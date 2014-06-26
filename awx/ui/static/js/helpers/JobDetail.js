/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobDetail.js
 *
 *  Helper moduler for JobDetails controller
 *
 */

/*
    # Playbook events will be structured to form the following hierarchy:
    # - playbook_on_start (once for each playbook file)
    #   - playbook_on_vars_prompt (for each play, but before play starts, we
    #     currently don't handle responding to these prompts)
    #   - playbook_on_play_start (once for each play)
    #     - playbook_on_import_for_host
    #     - playbook_on_not_import_for_host
    #     - playbook_on_no_hosts_matched
    #     - playbook_on_no_hosts_remaining
    #     - playbook_on_setup
    #       - runner_on*
    #     - playbook_on_task_start (once for each task within a play)
    #       - runner_on_failed
    #       - runner_on_ok
    #       - runner_on_error
    #       - runner_on_skipped
    #       - runner_on_unreachable
    #       - runner_on_no_hosts
    #       - runner_on_async_poll
    #       - runner_on_async_ok
    #       - runner_on_async_failed
    #       - runner_on_file_diff
    #     - playbook_on_notify (once for each notification from the play)
    #   - playbook_on_stats

*/

'use strict';

angular.module('JobDetailHelper', ['Utilities', 'RestServices', 'ModalDialog'])

.factory('DigestEvent', ['$rootScope', '$log', 'UpdatePlayStatus', 'UpdateHostStatus', 'AddHostResult',
    'GetElapsed', 'UpdateTaskStatus', 'DrawGraph', 'LoadHostSummary', 'JobIsFinished', 'AddNewTask',
function($rootScope, $log, UpdatePlayStatus, UpdateHostStatus, AddHostResult, GetElapsed,
    UpdateTaskStatus, DrawGraph, LoadHostSummary, JobIsFinished, AddNewTask) {
    return function(params) {

        var scope = params.scope,
            event = params.event;

        $log.debug('processing event: ' + event.id);

        switch (event.event) {
            case 'playbook_on_start':
                if (!JobIsFinished(scope)) {
                    scope.job_status.started = event.created;
                    scope.job_status.status = 'running';
                }
                break;

            case 'playbook_on_play_start':
                scope.jobData.plays[event.id] = {
                    id: event.id,
                    name: event.play,
                    created: event.created,
                    status: (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful',
                    elapsed: '00:00:00',
                    hostCount: 0,
                    fistTask: null,
                    unreachableCount: 0,
                    status_text: (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful',
                    tasks: {}
                };
                if (scope.activePlay) {
                    scope.jobData.plays[scope.activePlay].tasks = {};
                    scope.jobData.plays[scope.activePlay].playActiveClass = '';
                }
                scope.activePlay = event.id;
                scope.jobData.plays[scope.activePlay].playActiveClass = 'active';
                break;

            case 'playbook_on_setup':
                AddNewTask({ scope: scope, event: event });
                break;

            case 'playbook_on_task_start':
                AddNewTask({ scope: scope, event: event });
                break;

            case 'runner_on_ok':
            case 'runner_on_async_ok':
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: ( (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful' ),
                    id: event.id,
                    created: event.created,
                    modified: event.modified,
                    message: (event.event_data && event.event_data.res) ? event.event_data.res.msg : ''
                });
                break;

            case 'playbook_on_no_hosts_matched':
                UpdatePlayStatus({
                    scope: scope,
                    play_id: event.parent,
                    failed: true,
                    changed: false,
                    modified: event.modified,
                    status_text: 'failed- no hosts matched'
                });
                break;

            case 'runner_on_unreachable':
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: 'unreachable',
                    id: event.id,
                    created: event.created,
                    modified: event.modified,
                    message: ( (event.event_data && event.event_data.res) ? event.event_data.res.msg : '' )
                });
                break;

            case 'runner_on_error':
            case 'runner_on_async_failed':
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: 'failed',
                    id: event.id,
                    created: event.created,
                    modified: event.modified,
                    message: (event.event_data && event.event_data.res) ? event.event_data.res.msg : ''
                });
                break;

            case 'runner_on_no_hosts':
                UpdateTaskStatus({
                    scope: scope,
                    failed: event.failed,
                    changed: event.changed,
                    task_id: event.parent,
                    modified: event.modified,
                    no_hosts: true
                });
                break;

            case 'runner_on_skipped':
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: 'skipped',
                    id: event.id,
                    created: event.created,
                    modified: event.modified,
                    message: (event.event_data && event.event_data.res) ? event.event_data.res.msg : ''
                });
                break;

            // We will respond to the job status change event. No need to do this 2x.
            /*case 'playbook_on_stats':
                scope.job_status.finished = event.modified;
                scope.job_status.elapsed = GetElapsed({
                    start: scope.job_status.started,
                    end: scope.job_status.finished
                });
                scope.job_status.status = (event.failed) ? 'failed' : 'successful';
                scope.job_status.status_class = "";
                //LoadHostSummary({ scope: scope, data: event.event_data });
                //DrawGraph({ scope: scope, resize: true });
                break;*/
        }
    };
}])

.factory('JobIsFinished', [ function() {
    return function(scope) {
        return (scope.job_status.status === 'failed' || scope.job_status.status === 'canceled' ||
                    scope.job_status.status === 'error' || scope.job_status.status === 'successful');
    };
}])

.factory('GetElapsed', [ function() {
    return function(params) {
        var start = params.start,
            end = params.end,
            dt1, dt2, sec, hours, min;
        dt1 = new Date(start);
        dt2 = new Date(end);
        if ( dt2.getTime() !== dt1.getTime() ) {
            sec = Math.floor( (dt2.getTime() - dt1.getTime()) / 1000 );
            hours = Math.floor(sec / 3600);
            sec = sec - (hours * 3600);
            if (('' + hours).length < 2) {
                hours = ('00' + hours).substr(-2, 2);
            }
            min = Math.floor(sec / 60);
            sec = sec - (min * 60);
            min = ('00' + min).substr(-2,2);
            sec = ('00' + sec).substr(-2,2);
            return hours + ':' + min + ':' + sec;
        }
        else {
            return '00:00:00';
        }
    };
}])

.factory('AddNewTask', ['DrawGraph', 'UpdatePlayStatus', function(DrawGraph, UpdatePlayStatus) {
    return function(params) {
        var scope = params.scope,
            event = params.event;

        scope.jobData.plays[scope.activePlay].tasks[event.id] = {
            id: event.id,
            play_id: event.parent,
            name: event.event_display,
            status: ( (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful' ),
            created: event.created,
            modified: event.modified,
            hostCount: scope.jobData.plays[scope.activePlay].hostCount,
            reportedHosts: 0,
            successfulCount: 0,
            failedCount: 0,
            changedCount: 0,
            skippedCount: 0,
            successfulStyle: { display: 'none'},
            failedStyle: { display: 'none' },
            changedStyle: { display: 'none' },
            skippedStyle: { display: 'none' },
            hostResults: {}
        };

        if (scope.jobData.plays[scope.activePlay].firstTask === undefined || scope.jobData.plays[scope.activePlay].firstTask === null) {
            scope.jobData.plays[scope.activePlay].firstTask = event.id;
        }

        if (scope.activeTask && scope.jobData.plays[scope.activePlay].tasks[scope.activeTask] !== undefined) {
            scope.jobData.plays[scope.activePlay].tasks[scope.activeTask].taskActiveClass = '';
            scope.jobData.plays[scope.activePlay].tasks[scope.activeTask].hostResults = {};
        }
        scope.activeTask = event.id;
        scope.jobData.plays[scope.activePlay].tasks[scope.activeTask].taskActiveClass = 'active';

        UpdatePlayStatus({
            scope: scope,
            play_id: event.parent,
            failed: event.failed,
            changed: event.changed,
            modified: event.modified
        });

        /*if (scope.host_summary.total > 0) {
            DrawGraph({ scope: scope, resize: true });
        }*/
    };
}])

.factory('UpdateJobStatus', ['GetElapsed', 'Empty', function(GetElapsed, Empty) {
    return function(params) {
        var scope = params.scope,
            failed = params.failed,
            modified = params.modified,
            started =  params.started;

        if (failed && scope.job_status.status !== 'failed' && scope.job_status.status !== 'error' &&
            scope.job_status.status !== 'canceled') {
            scope.job_status.status = 'failed';
        }
        if (!Empty(modified)) {
            scope.job_status.finished = modified;
        }
        if (!Empty(started) && Empty(scope.job_status.started)) {
            scope.job_status.started = started;
        }
        if (!Empty(scope.job_status.finished) && !Empty(scope.job_status.started)) {
            scope.job_status.elapsed = GetElapsed({
                start: scope.job_status.started,
                end: scope.job_status.finished
            });
        }
    };
}])

// Update the status of a play
.factory('UpdatePlayStatus', ['GetElapsed', 'UpdateJobStatus', function(GetElapsed, UpdateJobStatus) {
    return function(params) {
        var scope = params.scope,
            failed = params.failed,
            changed = params.changed,
            id = params.play_id,
            modified = params.modified,
            no_hosts = params.no_hosts,
            status_text = params.status_text,
            play;

        if (scope.jobData.plays[id] !== undefined) {
            play = scope.jobData.plays[scope.activePlay];
            if (failed) {
                play.status = 'failed';
            }
            else if (play.status !== 'changed' && play.status !== 'failed') {
                // once the status becomes 'changed' or 'failed' don't modify it
                if (no_hosts) {
                    play.status = 'no-matching-hosts';
                }
                else {
                    play.status = (changed) ? 'changed' : (failed) ? 'failed' : 'successful';
                }
            }
            play.finished = modified;
            play.elapsed = GetElapsed({
                start: play.created,
                end: modified
            });
            play.status_text = (status_text) ? status_text : play.status;
        }

        UpdateJobStatus({
            scope: scope,
            failed: null,
            modified: modified
        });
    };
}])

.factory('UpdateTaskStatus', ['UpdatePlayStatus', 'GetElapsed', function(UpdatePlayStatus, GetElapsed) {
    return function(params) {
        var scope = params.scope,
            failed = params.failed,
            changed = params.changed,
            id = params.task_id,
            modified = params.modified,
            no_hosts = params.no_hosts,
            task;

        if (scope.jobData.plays[scope.activePlay].tasks[id] !== undefined) {
            task = scope.jobData.plays[scope.activePlay].tasks[scope.activeTask];
            if (no_hosts){
                task.status = 'no-matching-hosts';
            }
            else if (failed) {
                task.status = 'failed';
            }
            else if (task.status !== 'changed' && task.status !== 'failed') {
                // once the status becomes 'changed' or 'failed' don't modify it
                task.status = (failed) ? 'failed' : (changed) ? 'changed' : 'successful';
            }
            task.finished = params.modified;
            task.elapsed = GetElapsed({
                start: task.created,
                end: modified
            });

            UpdatePlayStatus({
                scope: scope,
                failed: failed,
                changed: changed,
                play_id: task.play_id,
                modified: modified,
                no_hosts: no_hosts
            });
        }
    };
}])

// Each time a runner event is received update host summary totals and the parent task
.factory('UpdateHostStatus', ['UpdateTaskStatus', 'AddHostResult',
    function(UpdateTaskStatus, AddHostResult) {
    return function(params) {
        var scope = params.scope,
            status = params.status,  // successful, changed, unreachable, failed, skipped
            name = params.name,
            event_id = params.id,
            host_id = params.host_id,
            task_id = params.task_id,
            modified = params.modified,
            created = params.created,
            msg = params.message;

        scope.host_summary.ok += (status === 'successful') ? 1 : 0;
        scope.host_summary.changed += (status === 'changed') ? 1 : 0;
        scope.host_summary.unreachable += (status === 'unreachable') ? 1 : 0;
        scope.host_summary.failed += (status === 'failed') ? 1 : 0;
        scope.host_summary.total  = scope.host_summary.ok + scope.host_summary.changed + scope.host_summary.unreachable +
            scope.host_summary.failed;

        if (scope.jobData.hostSummaries[host_id] !== undefined) {
            scope.jobData.hostSummaries[host_id].ok += (status === 'successful') ? 1 : 0;
            scope.jobData.hostSummaries[host_id].changed += (status === 'changed') ? 1 : 0;
            scope.jobData.hostSummaries[host_id].unreachable += (status === 'unreachable') ? 1 : 0;
            scope.jobData.hostSummaries[host_id].failed += (status === 'failed') ? 1 : 0;
        }
        else {
            scope.jobData.hostSummaries[host_id] = {
                id: host_id,
                name: name,
                ok: (status === 'successful') ? 1 : 0,
                changed: (status === 'changed') ? 1 : 0,
                unreachable: (status === 'unreachable') ? 1 : 0,
                failed: (status === 'failed') ? 1 : 0,
                status: (status === 'failed') ? 'failed' : 'successful'
            };
        }

        UpdateTaskStatus({
            scope: scope,
            task_id: task_id,
            failed: ((status === 'failed' || status === 'unreachable') ? true :false),
            changed: ((status === 'changed') ? true : false),
            modified: modified
        });

        AddHostResult({
            scope: scope,
            task_id: task_id,
            host_id: host_id,
            event_id: event_id,
            status: status,
            name: name,
            created: created,
            message: msg
        });
    };
}])

// Add a new host result
.factory('AddHostResult', ['SetTaskStyles', function(SetTaskStyles) {
    return function(params) {
        var scope = params.scope,
            task_id = params.task_id,
            host_id = params.host_id,
            event_id = params.event_id,
            status = params.status,
            created = params.created,
            name = params.name,
            msg = params.message,
            task;

        scope.jobData.plays[scope.activePlay].tasks[scope.activeTask].hostResults[event_id] = {
            id: event_id,
            status: status,
            host_id: host_id,
            task_id: task_id,
            name: name,
            created: created,
            msg: msg
        };

        // increment the unreachable count on the play
        if (status === 'unreachable' && scope.jobData.plays[scope.activePlay]) {
            scope.jobData.plays[scope.activePlay].unreachableCount++;
        }

        // update the task status bar
        if (scope.jobData.plays[scope.activePlay].tasks[task_id] !== undefined) {
            task = scope.jobData.plays[scope.activePlay].tasks[task_id];

            if (task_id === scope.jobData.plays[scope.activePlay].firstTask && status !== 'unreachable') {
                scope.jobData.plays[scope.activePlay].hostCount++;
                task.hostCount++;
            }

            task.reportedHosts += 1;
            task.failedCount += (status === 'failed') ? 1 : 0;
            task.changedCount += (status === 'changed') ? 1 : 0;
            task.successfulCount += (status === 'successful') ? 1 : 0;
            task.skippedCount += (status === 'skipped') ? 1 : 0;
            SetTaskStyles({
                task: task
            });
        }
    };
}])

.factory('SetTaskStyles', [ function() {
    return function(params) {
        var task = params.task,
            diff;

        //task = scope.jobData.plays[scope.activePlay].tasks[task_id];
        //task.hostCount = task.failedCount + task.changedCount + task.skippedCount + task.successfulCount;
        task.failedPct = (task.hostCount > 0) ? Math.ceil((100 * (task.failedCount / task.hostCount))) : 0;
        task.changedPct = (task.hostCount > 0) ? Math.ceil((100 * (task.changedCount / task.hostCount))) : 0;
        task.skippedPct = (task.hostCount > 0) ? Math.ceil((100 * (task.skippedCount / task.hostCount))) : 0;
        task.successfulPct = (task.hostCount > 0) ? Math.ceil((100 * (task.successfulCount / task.hostCount))) : 0;

        diff = (task.failedPct + task.changedPct + task.skippedPct + task.successfulPct) - 100;
        if (diff > 0) {
            if (task.failedPct > diff) {
                task.failedPct  = task.failedPct - diff;
            }
            else if (task.changedPct > diff) {
                task.changedPct = task.changedPct - diff;
            }
            else if (task.skippedPct > diff) {
                task.skippedPct = task.skippedPct - diff;
            }
            else if (task.successfulPct > diff) {
                task.successfulPct = task.successfulPct - diff;
            }
        }
        task.successfulStyle = (task.successfulPct > 0) ? { 'display': 'inline-block', 'width': task.successfulPct + "%" } : { 'display': 'none' };
        task.changedStyle = (task.changedPct > 0) ? { 'display': 'inline-block', 'width': task.changedPct + "%" } : { 'display': 'none' };
        task.skippedStyle = (task.skippedPct > 0) ? { 'display': 'inline-block', 'width': task.skippedPct + "%" } : { 'display': 'none' };
        task.failedStyle = (task.failedPct > 0) ? { 'display': 'inline-block', 'width': task.failedPct + "%" } : { 'display': 'none' };
    };
}])

// Call SelectPlay whenever the the activePlay needs to change
.factory('SelectPlay', ['SelectTask', 'LoadTasks', function(SelectTask, LoadTasks) {
    return function(params) {
        var scope = params.scope,
            id = params.id,
            callback = params.callback,
            clear = false;

        // Determine if the tasks and hostResults arrays should be initialized
        if (scope.search_all_hosts_name || scope.searchAllStatus === 'failed') {
            clear = true;
        }
        else {
            clear = (scope.activePlay === id) ? false : true;  //are we moving to a new play?
        }

        scope.activePlay = id;
        scope.plays.forEach(function(play, idx) {
            if (play.id === scope.activePlay) {
                scope.plays[idx].playActiveClass = 'active';
            }
            else {
                scope.plays[idx].playActiveClass = '';
            }
        });

        setTimeout(function() {
            scope.$apply(function() {
                LoadTasks({
                    scope: scope,
                    callback: callback,
                    clear: true
                });
            });
        });

    };
}])

.factory('LoadTasks', ['Rest', 'ProcessErrors', 'GetElapsed', 'SelectTask', 'SetTaskStyles', function(Rest, ProcessErrors, GetElapsed, SelectTask, SetTaskStyles) {
    return function(params) {
        var scope = params.scope,
            callback = params.callback,
            clear = params.clear,
            url;

        if (clear) {
            scope.tasks = [];
            scope.tasksMap = {};
        }

        if (scope.activePlay) {
            url = scope.job.url + 'job_tasks/?event_id=' + scope.activePlay;
            url += (scope.search_all_tasks.length > 0) ? '&id__in=' + scope.search_all_tasks.join() : '';
            url += (scope.searchAllStatus === 'failed') ? '&failed=true' : '';
            url += '&page_size=' + scope.tasksMaxRows + '&order_by=id';

            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    data.results.forEach(function(event, idx) {
                        var end, elapsed;

                        //if (!scope.plays[scope.playsMap[scope.activePlay]].firstTask) {
                        //    scope.plays[scope.playsMap[scope.activePlay]].firstTask = event.id;
                        //    scope.plays[scope.playsMap[scope.activePlay]].hostCount = (event.host_count) ? event.host_count : 0;
                        //}

                        if (idx < data.length - 1) {
                            // end date = starting date of the next event
                            end = data[idx + 1].created;
                        }
                        else {
                            // no next event (task), get the end time of the play
                            scope.plays.every(function(play) {
                                if (play.id === scope.activePlay) {
                                    end = play.finished;
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
                            hostCount: (event.host_count) ? event.host_count : 0,
                            reportedHosts: (event.reported_hosts) ? event.reported_hosts : 0,
                            successfulCount: (event.successful_count) ? event.successful_count : 0,
                            failedCount: (event.failed_count) ? event.failed_count : 0,
                            changedCount: (event.changed_count) ? event.changed_count : 0,
                            skippedCount: (event.skipped_count) ? event.skipped_count : 0,
                            taskActiveClass: ''
                        });

                        SetTaskStyles({
                            task: scope.tasks[scope.tasks.length - 1]
                        });
                    });

                    // set the active task
                    SelectTask({
                        scope: scope,
                        id: (scope.tasks.length > 0) ? scope.tasks[0].id : null,
                        callback: callback
                    });

                    $('#tasks-table-detail').mCustomScrollbar("update");
                })
                .error(function(data) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
        else {
            $('#tasks-table-detail').mCustomScrollbar("update");
            SelectTask({
                scope: scope,
                id: null,
                callback: callback
            });
        }
    };
}])

// Call SelectTask whenever the activeTask needs to change
.factory('SelectTask', ['LoadHosts', function(LoadHosts) {
    return function(params) {
        var scope = params.scope,
            id = params.id,
            callback = params.callback,
            clear=false;

        if (scope.search_all_hosts_name || scope.searchAllStatus === 'failed') {
            clear = true;
        }
        else {
            clear = (scope.activeTask === id) ? false : true;
        }

        scope.activeTask = id;
        scope.tasks.forEach(function(task, idx) {
            if (task.id === scope.activeTask) {
                scope.tasks[idx].taskActiveClass = 'active';
            }
            else {
                scope.tasks[idx].taskActiveClass = '';
            }
        });

        LoadHosts({
            scope: scope,
            callback: callback,
            clear: true
        });
    };
}])

// Refresh the list of hosts
.factory('LoadHosts', ['Rest', 'ProcessErrors', function(Rest, ProcessErrors) {
    return function(params) {
        var scope = params.scope,
            callback = params.callback,
            clear = params.clear,
            url;

        if (clear) {
            scope.hostResults = [];
            scope.hostResultsMap = {};
        }

        if (scope.activeTask) {
            // If we have a selected task, then get the list of hosts
            url = scope.job.related.job_events + '?parent=' + scope.activeTask + '&';
            url += (scope.search_all_hosts_name) ? 'host__name__icontains=' + scope.search_all_hosts_name + '&' : '';
            url += (scope.searchAllStatus === 'failed') ? 'failed=true&' : '';
            url += 'host__isnull=false&page_size=' + scope.hostTableRows + '&order_by=host__name';
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    data.results.forEach(function(event) {
                        scope.hostResults.push({
                            id: event.id,
                            status: (event.event === "runner_on_skipped") ? 'skipped' : (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful',
                            host_id: event.host,
                            task_id: event.parent,
                            name: event.event_data.host,
                            created: event.created,
                            msg: ( (event.event_data && event.event_data.res) ? event.event_data.res.msg : '' )
                        });
                    });
                    if (callback) {
                        scope.$emit(callback);
                    }
                    $('#hosts-table-detail').mCustomScrollbar("update");
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
        else {
            if (callback) {
                scope.$emit(callback);
            }
            $('#hosts-table-detail').mCustomScrollbar("update");
        }
    };
}])

// Refresh the list of hosts in the hosts summary section
.factory('ReloadHostSummaryList', ['Rest', 'ProcessErrors', function(Rest, ProcessErrors) {
    return function(params) {
        var scope = params.scope,
            callback = params.callback,
            url;

        url = scope.job.related.job_host_summaries + '?';
        url += (scope.search_all_hosts_name) ? 'host__name__icontains=' + scope.search_all_hosts_name + '&': '';
        url += (scope.searchAllStatus === 'failed') ? 'failed=true&' : '';
        url += 'page_size=' + scope.hostSummariesMaxRows + '&order_by=host__name';

        scope.hosts = [];

        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                data.results.forEach(function(event) {
                    scope.hosts.push({
                        id: event.host,
                        name: event.summary_fields.host.name,
                        ok: event.ok,
                        changed: event.changed,
                        unreachable: event.dark,
                        failed: event.failures,
                        status: (event.failed) ? 'failed' : 'successful'
                    });
                });
                $('#hosts-summary-table').mCustomScrollbar("update");
                if (callback) {
                    scope.$emit(callback);
                }
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + '. GET returned: ' + status });
            });
    };
}])

.factory('LoadHostSummary', [ function() {
    return function(params) {
        var scope = params.scope,
            data = params.data,
            host;
        scope.host_summary.ok = 0;
        for (host in data.ok) {
            scope.host_summary.ok += data.ok[host];
        }
        scope.host_summary.changed = 0;
        for (host in data.changed) {
            scope.host_summary.changed += data.changed[host];
        }
        scope.host_summary.unreachable = 0;
        for (host in data.dark) {
            scope.host_summary.unreachable += data.dark[host];
        }
        scope.host_summary.failed = 0;
        for (host in data.failures) {
            scope.host_summary.failed += data.failures[host];
        }
        scope.host_summary.total = scope.host_summary.ok + scope.host_summary.changed +
            scope.host_summary.unreachable + scope.host_summary.failed;
    };
}])

.factory('DrawGraph', [ function() {
    return function(params) {
        var scope = params.scope,
            resize = params.resize,
            width, height, svg_height, svg_width, svg_radius, svg, graph_data = [];

        // Ready the data
        if (scope.host_summary.ok) {
            graph_data.push({
                label: 'OK',
                value: (scope.host_summary.ok === scope.host_summary.total) ? 1 : scope.host_summary.ok,
                color: '#00aa00'
            });
        }
        if (scope.host_summary.changed) {
            graph_data.push({
                label: 'Changed',
                value: (scope.host_summary.changed === scope.host_summary.total) ? 1 : scope.host_summary.changed,
                color: '#FF9900'
            });
        }
        if (scope.host_summary.unreachable) {
            graph_data.push({
                label: 'Unreachable',
                value: (scope.host_summary.unreachable === scope.host_summary.total) ? 1 : scope.host_summary.unreachable,
                color: '#A9A9A9'
            });
        }
        if (scope.host_summary.failed) {
            graph_data.push({
                label: 'Failed',
                value: (scope.host_summary.failed === scope.host_summary.total) ? 1 : scope.host_summary.failed,
                color: '#aa0000'
            });
        }

        // Adjust the size
        width = $('#job-summary-container .job_well').width();
        height = $('#job-summary-container .job_well').height() - $('#summary-well-top-section').height() - $('#graph-section .header').outerHeight() - 15;
        svg_radius = Math.min(width, height);
        svg_width = width;
        svg_height = height;
        if (svg_height > 0 && svg_width > 0) {
            if (!resize && $('#graph-section svg').length > 0) {
                Donut3D.transition("completedHostsDonut", graph_data, Math.floor(svg_radius * 0.50), Math.floor(svg_radius * 0.25), 18, 0.4);
            }
            else {
                if ($('#graph-section svg').length > 0) {
                    $('#graph-section svg').remove();
                }
                svg = d3.select("#graph-section").append("svg").attr("width", svg_width).attr("height", svg_height);
                svg.append("g").attr("id","completedHostsDonut");
                Donut3D.draw("completedHostsDonut", graph_data, Math.floor(svg_width / 2), Math.floor(svg_height / 2), Math.floor(svg_radius * 0.50), Math.floor(svg_radius * 0.25), 18, 0.4);
                $('#graph-section .header .legend').show();
            }
        }
    };
}])

.factory('DrawPlays', [ function() {
    return function(params) {
        var scope = params.scope,
            idx = 0,
            result = [],
            newKeys = [],
            plays = JSON.parse(JSON.stringify(scope.jobData.plays)),
            keys = Object.keys(plays);
        keys.reverse();
        for (idx=0; idx < scope.playsMaxRows && idx < keys.length; idx++) {
            newKeys.push(keys[idx]);
        }
        newKeys.sort();
        idx = 0;
        while (idx < newKeys.length) {
            result.push(plays[newKeys[idx]]);
            idx++;
        }

        scope.plays = result;
        if (scope.liveEventProcessing) {
            scope.$emit('FixPlaysScroll');
        }
    };
}])

.factory('DrawTasks', [ function() {
    return function(params) {
        var scope = params.scope,
            result = [],
            idx, keys, newKeys, tasks;

        if (scope.activePlay) {
            tasks = JSON.parse(JSON.stringify(scope.jobData.plays[scope.activePlay].tasks));
            keys = Object.keys(tasks);
            keys.reverse();
            newKeys = [];
            for (idx=0; idx < scope.tasksMaxRows && idx < keys.length; idx++) {
                newKeys.push(keys[idx]);
            }
            newKeys.sort();
            idx = 0;
            while (idx < newKeys.length) {
                result.push(tasks[newKeys[idx]]);
                idx++;
            }
        }

        scope.tasks = result;
        if (scope.liveEventProcessing) {
            scope.$emit('FixTasksScroll');
        }
    };
}])

.factory('DrawHostResults', [ function() {
    return function(params) {
        var scope = params.scope,
            result = [],
            idx = 0,
            hostResults,
            keys;

        if (scope.activePlay && scope.activeTask) {
            hostResults = JSON.parse(JSON.stringify(scope.jobData.plays[scope.activePlay].tasks[scope.activeTask].hostResults));
            keys = Object.keys(hostResults);
            keys.sort(function(a,b) {
                if (hostResults[a].name > hostResults[b].name)
                    return -1;
                if (hostResults[a].name < hostResults[b].name)
                    return 1;
                // a must be equal to b
                return 0;
            });
            while (idx < keys.length && idx < scope.hostResultsMaxRows) {
                result.unshift(hostResults[keys[idx]]);
                idx++;
            }
        }
        scope.hostResults = result;
        if (scope.liveEventProcessing) {
            scope.$emit('FixHostResultsScroll');
        }
    };
}])

.factory('DrawHostSummaries', [ function() {
    return function(params) {
        var scope = params.scope,
            result = [],
            idx = 0,
            hostSummaries,
            keys;

        if (scope.activePlay && scope.activeTask) {
            hostSummaries = JSON.parse(JSON.stringify(scope.jobData.hostSummaries));
            keys = Object.keys(hostSummaries);

            keys.sort(function(a,b) {
                if (hostSummaries[a].name > hostSummaries[b].name)
                    return 1;
                if (hostSummaries[a].name < hostSummaries[b].name)
                    return -1;
                // a must be equal to b
                return 0;
            });

            while (idx < keys.length && idx < scope.hostSummariesMaxRows) {
                result.push(hostSummaries[keys[idx]]);
                idx++;
            }
        }
        scope.hosts = result;
        if (scope.liveEventProcessing) {
            scope.$emit('FixHostSummariesScroll');
        }
    };
}])


.factory('UpdateDOM', ['DrawPlays', 'DrawTasks', 'DrawHostResults', 'DrawHostSummaries', 'DrawGraph',
    function(DrawPlays, DrawTasks, DrawHostResults, DrawHostSummaries, DrawGraph) {
    return function(params) {
        var scope = params.scope;

        DrawPlays({ scope: scope });
        DrawTasks({ scope: scope });
        DrawHostResults({ scope: scope });
        DrawHostSummaries({ scope: scope });

        if (scope.host_summary.total > 0) {
            DrawGraph({ scope: scope, resize: true });
        }
    };
}])

.factory('FilterAllByHostName', ['Rest', 'GetBasePath', 'ProcessErrors', 'SelectPlay', function(Rest, GetBasePath, ProcessErrors, SelectPlay) {
    return function(params) {
        var scope = params.scope,
            host = params.host,
            newActivePlay,
            url = scope.job.related.job_events + '?event__icontains=runner&host_name__icontains=' + host + '&parent__isnull=false';

        scope.search_all_tasks = [];
        scope.search_all_plays = [];

        if (scope.removeAllPlaysReady) {
            scope.removeAllPlaysReady();
        }
        scope.removeAllPlaysReady = scope.$on('AllPlaysReady', function() {
            if (scope.activePlay) {
                setTimeout(function() {
                    SelectPlay({
                        scope: scope,
                        id: newActivePlay
                    });
                }, 500);
            }
            else {
                scope.tasks = [];
                scope.hostResults = [];
            }
        });

        if (scope.removeAllTasksReady) {
            scope.removeAllTasksReady();
        }
        scope.removeAllTasksReady = scope.$on('AllTasksReady', function() {
            if (scope.search_all_tasks.length > 0) {
                url = scope.job.related.job_events + '?id__in=' + scope.search_all_tasks.join();
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data) {
                        if (data.count > 0) {
                            data.results.forEach(function(row) {
                                if (row.parent && scope.search_all_plays.indexOf(row.parent) < 0) {
                                    scope.search_all_plays.push(row.parent);
                                }
                            });
                            if (scope.search_all_plays.length > 0) {
                                scope.search_all_plays.sort();
                                newActivePlay = scope.search_all_plays[0];
                            }
                            else {
                                newActivePlay = null;
                            }
                        }
                        scope.$emit('AllPlaysReady');
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                    });
            }
            else {
                newActivePlay = null;
                scope.search_all_plays.push(0);
                scope.$emit('AllPlaysReady');
            }
        });

        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                if (data.count > 0) {
                    data.results.forEach(function(row) {
                        if (scope.search_all_tasks.indexOf(row.parent) < 0) {
                            scope.search_all_tasks.push(row.parent);
                        }
                    });
                    if (scope.search_all_tasks.length > 0) {
                        scope.search_all_tasks.sort();
                    }
                }
                scope.$emit('AllTasksReady');
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + '. GET returned: ' + status });
            });
    };
}])

.factory('ViewHostResults', ['$log', 'CreateDialog', 'Rest', 'ProcessErrors', 'Wait', function($log, CreateDialog, Rest, ProcessErrors, Wait) {
    return function(params) {
        var scope = params.scope,
            my_scope = params.scope.$new(),
            id = params.id,
            url;

        function parseJSON(obj) {
            var html="", keys;
            if (typeof obj === "object") {
                html += "<table class=\"object-list\">\n";
                html += "<tbody>\n";
                keys = Object.keys(obj).sort();
                keys.forEach(function(key) {
                    if (typeof obj[key] === "boolean" || typeof obj[key] === "number" || typeof obj[key] === "string") {
                        html += "<tr><td class=\"key\">" + key + ":</td><td class=\"value";
                        html += (key === "results" || key === "stdout" || key === "stderr") ? " mono-space" : "";
                        html += "\">";
                        html += (key === "status") ? "<i class=\"fa icon-job-" + obj[key] + "\"></i> " + obj[key] : obj[key];
                        html += "</td></tr>\n";
                    }
                    else if (obj[key] === null || obj[key] === undefined) {
                        // html += "<tr><td class=\"key\">" + key + ":</td><td class=\"value\">null</td></tr>\n";
                    }
                    else if (typeof obj[key] === "object" && Array.isArray(obj[key])) {
                        html += "<tr><td class=\"key\">" + key + ":</td><td class=\"value";
                        html += (key === "results" || key === "stdout" || key === "stderr") ? " mono-space" : "";
                        html += "\">";
                        obj[key].forEach(function(row) {
                            html += "<p>" + row + "</p>";
                        });
                        html += "</td></tr>\n";
                    }
                    else if (typeof obj[key] === "object") {
                        html += "<tr><td class=\"key\">" + key + ":</td><td class=\"nested-table\">\n" + parseJSON(obj[key]) + "</td></tr>\n";
                    }
                });
                html += "</tbody>\n";
                html += "</table>\n";
            }
            return html;
        }

        if (my_scope.removeDataReady) {
            my_scope.removeDataReady();
        }
        my_scope.removeDataReady = my_scope.$on('DataReady', function(e, event_data, host) {
            //var html = "<div class=\"title-section\">\n";
            //html += "<h4>" + host.name + "</h4>\n";
            //html += (host.description && host.description !== "imported") ? "<h5>" + host.description + "</h5>" : "";
            //html += "<p>Event " + id + " details:</p>\n";
            //html += "</div>\n";
            var html = "<div class=\"results\">\n";
            event_data.host = host.name;
            html += parseJSON(event_data);
            html += "<div class=\"spacer\"></div>\n";
            html += "</div>\n";

            $('#event-viewer-dialog').empty().html(html);

            CreateDialog({
                scope: my_scope,
                width: 600,
                height: 550,
                minWidth: 450,
                callback: 'ModalReady',
                id: 'event-viewer-dialog',
                title: 'Host Results',
                onOpen: function() {
                    $('#dialog-ok-button').focus();
                }
            });
        });

        if (my_scope.removeModalReady) {
            my_scope.removeModalReady();
        }
        my_scope.removeModalReady = my_scope.$on('ModalReady', function() {
            Wait('stop');
            $('#event-viewer-dialog').dialog('open');
        });

        url = scope.job.related.job_events + "?id=" + id;
        Wait('start');
        Rest.setUrl(url);
        Rest.get()
            .success( function(data) {
                var key;
                Wait('stop');
                if (data.results.length > 0 && data.results[0].event_data.res) {
                    for (key in data.results[0].event_data) {
                        if (key !== "res") {
                            data.results[0].event_data.res[key] = data.results[0].event_data[key];
                        }
                    }
                    if (data.results[0].event_data.res.ansible_facts) {
                        delete data.results[0].event_data.res.ansible_facts;
                    }
                    data.results[0].event_data.res.status = (data.results[0].event === "runner_on_skipped") ? 'skipped' : (data.results[0].failed) ? 'failed' :
                        (data.results[0].changed) ? 'changed' : 'successful';
                    my_scope.$emit('DataReady', data.results[0].event_data.res, data.results[0].summary_fields.host, data.results[0].id);
                }
                else {
                    data.results[0].event_data.status = (data.results[0].event === "runner_on_skipped") ? 'skipped' : (data.results[0].failed) ? 'failed' :
                        (data.results[0].changed) ? 'changed' : 'successful';
                    my_scope.$emit('DataReady', data.results[0].event_data, data.results[0].summary_fields.host, data.results[0].id);
                }
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + '. GET returned: ' + status });
            });

        scope.modalOK = function() {
            $('#event-viewer-dialog').dialog('close');
            my_scope.$destroy();
        };
    };
}]);