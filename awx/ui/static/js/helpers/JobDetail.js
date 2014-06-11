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

angular.module('JobDetailHelper', ['Utilities', 'RestServices'])

.factory('DigestEvents', ['UpdatePlayStatus', 'UpdateHostStatus', 'AddHostResult', 'SelectPlay', 'SelectTask',
    'GetHostCount', 'GetElapsed', 'UpdateTaskStatus', 'DrawGraph', 'LoadHostSummary',
function(UpdatePlayStatus, UpdateHostStatus, AddHostResult, SelectPlay, SelectTask, GetHostCount, GetElapsed,
    UpdateTaskStatus, DrawGraph, LoadHostSummary) {
    return function(params) {

        var scope = params.scope,
            events = params.events;

        events.forEach(function(event) {
            var hostCount;

            if (event.event === 'playbook_on_start') {
                if (scope.job_status.status!== 'failed' && scope.job_status.status !== 'canceled' &&
                    scope.job_status.status !== 'error' && scope.job_status !== 'successful') {
                    scope.job_status.started = event.created;
                    scope.job_status.status = 'running';
                }
            }

            if (event.event === 'playbook_on_play_start') {
                scope.plays[event.id] = {
                    id: event.id,
                    name: event.play,
                    created: event.created,
                    status: (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'none',
                    elapsed: '00:00:00'
                };
                SelectPlay({
                    scope: scope,
                    id: event.id
                });
            }
            if (event.event === 'playbook_on_setup') {
                if (scope.activePlay === event.parent) {
                    hostCount = GetHostCount({
                        scope: scope,
                        play_id: event.parent
                    });
                    scope.tasks[event.id] = {
                        id: event.id,
                        play_id: event.parent,
                        name: event.event_display,
                        status: ( (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful' ),
                        created: event.created,
                        modified: event.modified,
                        hostCount: hostCount,
                        reportedHosts: 0,
                        successfulCount: 0,
                        failedCount: 0,
                        changedCount: 0,
                        skippedCount: 0,
                        successfulStyle: { display: 'none'},
                        failedStyle: { display: 'none' },
                        changedStyle: { display: 'none' },
                        skippedStyle: { display: 'none' }
                    };
                    SelectTask({
                        scope: scope,
                        id: event.id
                    });
                }
                UpdatePlayStatus({
                    scope: scope,
                    play_id: event.parent,
                    failed: event.failed,
                    changed: event.changed,
                    modified: event.modified
                });
            }
            if (event.event === 'playbook_on_no_hosts_matched') {
                UpdatePlayStatus({
                    scope: scope,
                    play_id: event.parent,
                    failed: true,
                    changed: false,
                    modified: event.modified,
                    status_text: 'failed- no hosts matched'
                });
            }
            if (event.event === 'playbook_on_task_start') {
                if (scope.activePlay === event.parent) {
                    hostCount = GetHostCount({
                        scope: scope,
                        play_id: event.parent
                    });
                    scope.tasks[event.id] = {
                        id: event.id,
                        name: event.task,
                        play_id: event.parent,
                        status: ( (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful' ),
                        role: event.role,
                        created: event.created,
                        modified: event.modified,
                        hostCount: hostCount,
                        reportedHosts: 0,
                        successfulCount: 0,
                        failedCount: 0,
                        changedCount: 0,
                        skippedCount: 0,
                        successfulStyle: { display: 'none'},
                        failedStyle: { display: 'none' },
                        changedStyle: { display: 'none' },
                        skippedStyle: { display: 'none' }
                    };
                    SelectTask({
                        scope: scope,
                        id: event.id
                    });
                }
                if (event.role) {
                    scope.hasRoles = true;
                }
                UpdatePlayStatus({
                    scope: scope,
                    play_id: event.parent,
                    failed: event.failed,
                    changed: event.changed,
                    modified: event.modified
                });
            }

            if (event.event === 'runner_on_unreachable') {
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: 'unreachable',
                    event_id: event.id,
                    created: event.created,
                    modified: event.modified,
                    message: ( (event.event_data && event.event_data.res) ? event.event_data.res.msg : '' )
                });

            }
            if (event.event === 'runner_on_error' || event.event === 'runner_on_async_failed') {
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: 'failed',
                    event_id: event.id,
                    created: event.created,
                    modified: event.modified,
                    message: (event.event_data && event.event_data.res) ? event.event_data.res.msg : ''
                });
            }
            if (event.event === 'runner_on_no_hosts') {
                UpdateTaskStatus({
                    scope: scope,
                    failed: event.failed,
                    changed: event.changed,
                    task_id: event.parent,
                    modified: event.modified,
                    no_hosts: true
                });
            }
            if (event.event === 'runner_on_skipped') {
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: 'skipped',
                    event_id: event.id,
                    created: event.created,
                    modified: event.modified,
                    message: (event.event_data && event.event_data.res) ? event.event_data.res.msg : ''
                });
            }
            if (event.event === 'runner_on_ok' || event.event === 'runner_on_async_ok') {
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: ( (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful' ),
                    event_id: event.id,
                    created: event.created,
                    modified: event.modified,
                    message: (event.event_data && event.event_data.res) ? event.event_data.res.msg : ''
                });
            }
            if (event.event === 'playbook_on_stats') {
                scope.job_status.finished = event.modified;
                scope.job_status.elapsed = GetElapsed({
                    start: scope.job_status.started,
                    end: scope.job_status.finished
                });
                scope.job_status.status = (event.failed) ? 'failed' : 'successful';
                scope.job_status.status_class = "";
                scope.host_summary = {};
                LoadHostSummary({ scope: scope, data: event.event_data });
                DrawGraph({ scope: scope, resize: true });
            }
        });
    };
}])

//Get the # of expected hosts for a task by looking at the number
//on the very first task for a play
.factory('GetHostCount', [ 'FindFirstTaskofPlay', function(FindFirstTaskofPlay) {
    return function(params) {
        var scope = params.scope,
            task_id = FindFirstTaskofPlay({ scope: scope });
        if (task_id) {
            return scope.tasks[task_id].hostCount;
        }
        return 0;
    };
}])

.factory('FindFirstTaskofPlay', function() {
    return function(params) {
        var scope = params.scope,
            taskIds;
        taskIds = Object.keys(scope.tasks);
        if (taskIds.length > 0) {
            return scope.tasks[taskIds.length - 1].id;
        }
        return null;
    };
})

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
            play = scope.plays[id];

        if (failed) {
            scope.plays[id].status = 'failed';
        }
        else if (play.status !== 'changed' && play.status !== 'failed') {
            // once the status becomes 'changed' or 'failed' don't modify it
            if (no_hosts) {
                scope.plays[id].status = 'no-matching-hosts';
            }
            else {
                scope.plays[id].status = (changed) ? 'changed' : (failed) ? 'failed' : 'successful';
            }
        }
        scope.plays[id].finished = modified;
        scope.plays[id].elapsed = GetElapsed({
            start: play.created,
            end: modified
        });
        scope.plays[id].status_text = (status_text) ? status_text : scope.plays[id].status;
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
            task = scope.tasks[scope.activePlay][id];
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
    };
}])

// Each time a runner event is received update host summary totals and the parent task
.factory('UpdateHostStatus', ['UpdateTaskStatus', 'AddHostResult',
    function(UpdateTaskStatus, AddHostResult) {
    return function(params) {
        var scope = params.scope,
            status = params.status,  // successful, changed, unreachable, failed, skipped
            name = params.name,
            event_id = params.event_id,
            host_id = params.host_id,
            task_id = params.task_id,
            modified = params.modified,
            created = params.created,
            msg = params.message,
            host;

        if (scope.hostsMap[host_id]) {
            host = scope.hosts[scope.hostsMap[host_id]];
            host.ok += (status === 'successful') ? 1 : 0;
            host.changed += (status === 'changed') ? 1 : 0;
            host.unreachable += (status === 'unreachable') ? 1 : 0;
            host.failed += (status === 'failed') ? 1 : 0;
        }
        else {
            // Totals for the summary graph
            scope.host_summary.total += 1;
            scope.host_summary.ok += (status === 'successful') ? 1 : 0;
            scope.host_summary.changed += (status === 'changed') ? 1 : 0;
            scope.host_summary.unreachable += (status === 'unreachable') ? 1 : 0;
            scope.host_summary.failed += (status === 'failed') ? 1 : 0;
            scope.hosts.push({
                id: host_id,
                name: name,
                ok: (status === 'successful') ? 1 : 0,
                changed: (status === 'changed') ? 1 : 0,
                unreachable: (status === 'unreachable') ? 1 : 0,
                failed: (status === 'failed') ? 1 : 0
            });

            scope.hosts.sort(function (a, b) {
                if (a.name > b.name)
                    return 1;
                if (a.name < b.name)
                    return -1;
                // a must be equal to b
                return 0;
            });

            // prune the hosts array and rebuild the map
            if (scope.hosts.length > scope.hostSummaryTableRows) {
                scope.hosts.pop();
            }
            scope.hostsMap = {};
            scope.hosts.forEach(function(host, idx){
                scope.hostsMap[host.id] = idx;
            });
            $('#tasks-table-detail').mCustomScrollbar("update");
            /*setTimeout( function() {
                scope.auto_scroll = true;
                $('#hosts-summary-table').mCustomScrollbar("scrollTo", "bottom");
            }, 700);*/
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
.factory('AddHostResult', ['FindFirstTaskofPlay', function(FindFirstTaskofPlay) {
    return function(params) {
        var scope = params.scope,
            task_id = params.task_id,
            host_id = params.host_id,
            event_id = params.event_id,
            status = params.status,
            created = params.created,
            name = params.name,
            msg = params.message,
            pId, diff, task, play_id, first;

        if (scope.activeTask === task_id && !scope.hostResultsMap[host_id]) {
            // the event applies to the currently selected task
            scope.hostResults.push({
                id: event_id,
                status: status,
                host_id: host_id,
                task_id: task_id,
                name: name,
                created: created,
                msg: msg
            });
            scope.hostResults.sort(function(a,b) {
                if (a.name < b.name) {
                    return -1;
                }
                if (a.name > b.name) {
                    return 1;
                }
                return 0;
            });
            // Keep the list pruned to a limited # of hosts
            if (scope.hostResults.length > scope.hostTableRows) {
                scope.hostResults.splice(0,1);
            }
        }

        // get the correct play_id for this event. the task_id is always correct/available, but sometimes
        // the event does not have a play_id
        for (pId in scope.tasks) {
            if (scope.tasks[pId][task_id]) {
                play_id = pId;
            }
        }

        first = FindFirstTaskofPlay({
            scope: scope,
            play_id: play_id
        });

        task = scope.tasks[play_id][task_id];
        if (task_id === first) {
            task.hostCount += 1;
        }
        task.reportedHosts++;
        task.failedCount += (status === 'failed' || status === 'unreachable') ? 1 : 0;
        task.changedCount += (status === 'changed') ? 1 : 0;
        task.successfulCount += (status === 'successful') ? 1 : 0;
        task.skippedCount += (status === 'skipped') ? 1 : 0;

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
        task.successfulStyle = (task.successfulPct > 0) ? { display: 'inline-block', width: task.successfulPct + '%' } : { display: 'none' };
        task.changedStyle = (task.changedPct > 0) ? { display: 'inline-block', width: task.changedPct + '%' } : { display: 'none' };
        task.skippedStyle = (task.skippedPct > 0) ? { display: 'inline-block', width: task.skippedPct + '%' } : { display: 'none' };
        task.failedStyle = (task.failedPct > 0) ? { display: 'inline-block', width: task.failedPct + '%' } : { display: 'none' };
        $('#' + task.id + '-' + task.play_id + '-' + 'successful-bar').css(task.successfulStyle);
        $('#' + task.id + '-' + task.play_id + '-' + 'changed-bar').css(task.changedStyle);
        $('#' + task.id + '-' + task.play_id + '-' + 'skipped-bar').css(task.skippedStyle);
        $('#' + task.id + '-' + task.play_id + '-' + 'failed-bar').css(task.failedStyle);
    };
}])

// Call SelectPlay whenever the the activePlay needs to change
.factory('SelectPlay', ['SelectTask', 'LoadTasks', function(SelectTask, LoadTasks) {
    return function(params) {
        var scope = params.scope,
            id = params.id;

        if (scope.plays[scope.activePlay]) {
            scope.plays[scope.activePlay].playActiveClass = '';
        }
        scope.plays[id].playActiveClass = 'active';
        scope.activePlay = id;
        scope.activePlayName = scope.plays[id].name;

        LoadTasks({
            scope: scope
        });

    };
}])

.factory('LoadTasks', ['Rest', 'ProcessErrors', 'GetElapsed', 'SelectTask', function(Rest, ProcessErrors, GetElapsed, SelectTask) {
    return function(params) {
        var scope = params.scope,
            callback = params.callback,
            url = scope.job.related.job_tasks + '?parent=' + scope.activePlay + '&order_by=id';

        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                var tIds, lastId;
                scope.tasks = {};
                data.results.forEach(function(event, idx) {
                    var end, elapsed;

                    if (idx < data.results.length - 1) {
                        // end date = starting date of the next event
                        end = data.results[idx + 1].created;
                    }
                    else {
                        // no next event (task), get the end time of the play
                        end = scope.plays[scope.activePlay].finished;
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

                    scope.tasks[event.id] = {
                        id: event.id,
                        play_id: event.id,
                        name: event.event_display,
                        status: ( (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful' ),
                        created: event.created,
                        modified: event.modified,
                        finished: end,
                        elapsed: elapsed,
                        hostCount: 0,             // hostCount,
                        reportedHosts: 0,
                        successfulCount: 0,
                        failedCount: 0,
                        changedCount: 0,
                        skippedCount: 0,
                        successfulStyle: { display: 'none'},
                        failedStyle: { display: 'none' },
                        changedStyle: { display: 'none' },
                        skippedStyle: { display: 'none' },
                        taskActiveClass: ''
                    };
                });

                // set the active task
                tIds = Object.keys(scope.tasks);
                lastId = (tIds.length > 0) ? tIds[tIds.length - 1] : null;
                SelectTask({
                    scope: scope,
                    id: lastId
                });

                if (callback) {
                    scope.$emit(callback);
                }
            })
            .error(function(data) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + '. GET returned: ' + status });
            });
    };
}])

// Call SelectTask whenever the activeTask needs to change
.factory('SelectTask', ['LoadHosts', function(LoadHosts) {
    return function(params) {
        var scope = params.scope,
            id = params.id,
            callback = params.callback;

        scope.tasks[scope.activePlay][scope.activeTask].taskActiveClass = '';
        scope.tasks[scope.activePlay][id].taskActiveClass = 'active';
        scope.activeTask = id;
        scope.activeTaskName = scope.tasks[scope.activePlay][id].name;

        if (callback) {
            callback();
        }

        $('#tasks-table-detail').mCustomScrollbar("update");
        setTimeout( function() {
            scope.auto_scroll = true;
            $('#tasks-table-detail').mCustomScrollbar("scrollTo", "bottom");
        }, 700);

        LoadHosts({
            scope: scope
        });
    };
}])

// Refresh the list of hosts
.factory('LoadHosts', ['Rest', 'ProcessErrors', 'SelectHost', function(Rest, ProcessErrors, SelectHost) {
    return function(params) {
        var scope = params.scope,
            callback = params.callback,
            url;
        scope.hostResults = [];
        scope.hostResultsMap = {};
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
                        status: ( (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful' ),
                        host_id: event.host,
                        task_id: event.parent,
                        name: event.event_data.host,
                        created: event.created,
                        msg: ( (event.event_data && event.event_data.res) ? event.event_data.res.msg : '' )
                    });
                    scope.hostResultsMap[event.id] = scope.hostResults.length - 1;
                });
                SelectHost({ scope: scope });
                if (callback) {
                    scope.$emit(callback);
                }
                else {
                    scope.$emit('InitialDataLoaded');
                }
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + '. GET returned: ' + status });
            });
    };
}])

.factory('SelectHost', [ function() {
    return function(params) {
        var scope = params.scope;
        $('#tasks-table-detail').mCustomScrollbar("update");
        setTimeout( function() {
            scope.auto_scroll = true;
            $('#hosts-table-detail').mCustomScrollbar("scrollTo", "bottom");
        }, 700);
    };
}])

// Refresh the list of hosts in the hosts summary section
.factory('ReloadHostSummaryList', ['Rest', 'ProcessErrors', function(Rest, ProcessErrors) {
    return function(params) {
        var scope = params.scope,
            callback = params.callback,
            url;
        scope.hosts = [];
        scope.hostsMap = {};
        url = scope.job.related.job_host_summaries + '?';
        url += (scope.search_all_hosts_name) ? 'host__name__icontains=' + scope.search_all_hosts_name + '&': '';
        url += (scope.searchAllStatus === 'failed') ? 'failed=true&' : '';
        url += 'page_size=' + scope.hostSummaryTableRows + '&order_by=host__name';
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
                        failed: event.failures
                    });
                    scope.hostsMap[event.id] = scope.hosts.length - 1;
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
            data = params.data;
        scope.host_summary.ok = Object.keys(data.ok).length;
        scope.host_summary.changed = Object.keys(data.changed).length;
        scope.host_summary.unreachable = Object.keys(data.dark).length;
        scope.host_summary.failed = Object.keys(data.failures).length;
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
                color: '#5bb75b'
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
                color: '#DA4D49'
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
        });

        if (scope.removeAllTasksReady) {
            scope.removeAllTasksReady();
        }
        scope.removeAllTasksReady = scope.$on('AllTasksReady', function() {
            url = scope.job.related.job_events + '?id__in=' + scope.search_all_tasks.join();
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    if (data.count > 0) {
                        data.results.forEach(function(row) {
                            if (row.parent) {
                                scope.search_all_plays.push(row.parent);
                            }
                        });
                        if (scope.search_all_plays.length > 0) {
                            scope.search_all_plays.sort();
                            newActivePlay = scope.search_all_plays[scope.search_all_plays.length - 1];
                        }
                        else {
                            newActivePlay = null;
                        }
                    }
                    else {
                        scope.search_all_plays.push(0);
                    }
                    scope.$emit('AllPlaysReady');
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        });

        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                if (data.count > 0) {
                    data.results.forEach(function(row) {
                        if (row.parent) {
                            scope.search_all_tasks.push(row.parent);
                        }
                    });
                    if (scope.search_all_tasks.length > 0) {
                        scope.search_all_tasks.sort();
                    }
                }
                else {
                    scope.search_all_tasks.push(0);
                }
                scope.$emit('AllTasksReady');
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + '. GET returned: ' + status });
            });
    };
}]);