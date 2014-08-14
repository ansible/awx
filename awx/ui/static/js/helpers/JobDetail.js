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
    'GetElapsed', 'UpdateTaskStatus', 'DrawGraph', 'LoadHostSummary', 'JobIsFinished', 'AddNewTask', 'AddNewPlay',
function($rootScope, $log, UpdatePlayStatus, UpdateHostStatus, AddHostResult, GetElapsed,
    UpdateTaskStatus, DrawGraph, LoadHostSummary, JobIsFinished, AddNewTask, AddNewPlay) {
    return function(params) {

        var scope = params.scope,
            event = params.event,
            msg;

        $log.debug('processing event: ' + event.id);

        function getMsg(event) {
            var msg = '';
            if (event.event_data && event.event_data.res) {
                if (typeof event.event_data.res === 'object') {
                    msg = event.event_data.res.msg;
                } else {
                    msg = event.event_data.res;
                }
            }
            return msg;
        }

        switch (event.event) {
            case 'playbook_on_start':
                if (!JobIsFinished(scope)) {
                    scope.job_status.started = event.created;
                    scope.job_status.status = 'running';
                }
                break;

            case 'playbook_on_play_start':
                AddNewPlay({ scope: scope, event: event });
                break;

            case 'playbook_on_setup':
                AddNewTask({ scope: scope, event: event });
                break;

            case 'playbook_on_task_start':
                AddNewTask({ scope: scope, event: event });
                break;

            case 'runner_on_ok':
            case 'runner_on_async_ok':
                msg = getMsg(event);
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: ( (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful' ),
                    id: event.id,
                    created: event.created,
                    modified: event.modified,
                    message: msg,
                    item: (event.event_data && event.event_data.res) ? event.event_data.res.item : ''
                });
                break;

            case 'playbook_on_no_hosts_matched':
                UpdatePlayStatus({
                    scope: scope,
                    play_id: event.parent,
                    failed: false,
                    changed: false,
                    modified: event.modified,
                    no_hosts: true
                });
                break;

            case 'runner_on_unreachable':
                msg = getMsg(event);
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: 'unreachable',
                    id: event.id,
                    created: event.created,
                    modified: event.modified,
                    message: msg,
                    item: (event.event_data && event.event_data.res) ? event.event_data.res.item : ''
                });
                break;

            case 'runner_on_error':
            case 'runner_on_async_failed':
                msg = getMsg(event);
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: 'failed',
                    id: event.id,
                    created: event.created,
                    modified: event.modified,
                    message: msg,
                    item: (event.event_data && event.event_data.res) ? event.event_data.res.item : ''
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
                msg = getMsg(event);
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: 'skipped',
                    id: event.id,
                    created: event.created,
                    modified: event.modified,
                    message: msg,
                    item: (event.event_data && event.event_data.res) ? event.event_data.res.item : ''
                });
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

.factory('SetActivePlay', [ function() {
    return function(params) {
        //find the most recent task in the list of 'active' tasks

        var scope = params.scope,
            activeList = [],
            newActivePlay,
            key;

        for (key in scope.jobData.plays) {
            if (scope.jobData.plays[key].taskCount > 0) {
                activeList.push(key);
            }
        }

        if (activeList.length > 0) {
            newActivePlay = scope.jobData.plays[activeList[activeList.length - 1]].id;
            if (newActivePlay && scope.activePlay && newActivePlay !== scope.activePlay) {
                scope.jobData.plays[scope.activePlay].tasks = {};
                scope.jobData.plays[scope.activePlay].playActiveClass = '';
                scope.activeTask = null;
            }
            if (newActivePlay) {
                scope.activePlay = newActivePlay;
                scope.jobData.plays[scope.activePlay].playActiveClass = 'active';
            }
        }
    };
}])

.factory('SetActiveTask', [ function() {
    return function(params) {
        //find the most recent task in the list of 'active' tasks
        var scope = params.scope,
            key,
            newActiveTask,
            activeList = [];

        for (key in scope.jobData.plays[scope.activePlay].tasks) {
            if (scope.jobData.plays[scope.activePlay].tasks[key].reportedHosts > 0 || scope.jobData.plays[scope.activePlay].tasks[key].status === 'no-matching-hosts') {
                activeList.push(key);
            }
        }

        if (activeList.length > 0) {
            newActiveTask = scope.jobData.plays[scope.activePlay].tasks[activeList[activeList.length - 1]].id;
            if (newActiveTask && scope.activeTask && newActiveTask !== scope.activeTask) {
                if (scope.activeTask && scope.jobData.plays[scope.activePlay].tasks[scope.activeTask] !== undefined) {
                    scope.jobData.plays[scope.activePlay].tasks[scope.activeTask].taskActiveClass = '';
                    scope.jobData.plays[scope.activePlay].tasks[scope.activeTask].hostResults = {};
                }
            }
            if (newActiveTask) {
                scope.activeTask = newActiveTask;
                scope.jobData.plays[scope.activePlay].tasks[scope.activeTask].taskActiveClass = 'active';
            }
        }
    };
}])

.factory('AddNewPlay', ['SetActivePlay', function(SetActivePlay) {
    return function(params) {
        var scope = params.scope,
            event = params.event,
            status, status_text;

        status = (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful';
        status_text = (event.failed) ? 'Failed' : (event.changed) ? 'Changed' : 'OK';

        scope.jobData.plays[event.id] = {
            id: event.id,
            name: event.play,
            created: event.created,
            status: status,
            status_text: status_text,
            elapsed: '00:00:00',
            hostCount: 0,
            taskCount: 0,
            fistTask: null,
            unreachableCount: 0,
            status_tip: "Event ID: " + event.id + "<br />Status: " + status_text,
            tasks: {}
        };

        SetActivePlay({ scope: scope });
    };
}])

.factory('AddNewTask', ['DrawGraph', 'UpdatePlayStatus', 'SetActivePlay', 'SetActiveTask', function(DrawGraph, UpdatePlayStatus, SetActivePlay, SetActiveTask) {
    return function(params) {
        var scope = params.scope,
            event = params.event,
            status, status_text;

        status = (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful';
        status_text = (event.failed) ? 'Failed' : (event.changed) ? 'Changed' : 'OK';

        scope.jobData.plays[event.parent].tasks[event.id] = {
            id: event.id,
            play_id: event.parent,
            name: (event.task) ? event.task : event.event_display,
            status: status,
            status_text: status_text,
            status_tip: "Event ID: " + event.id + "<br />Status: " + status_text,
            created: event.created,
            modified: event.modified,
            hostCount: (scope.jobData.plays[event.parent]) ? scope.jobData.plays[event.parent].hostCount : 0,
            reportedHosts: 0,
            successfulCount: 0,
            failedCount: 0,
            changedCount: 0,
            skippedCount: 0,
            unreachableCount: 0,
            successfulStyle: { display: 'none'},
            failedStyle: { display: 'none' },
            changedStyle: { display: 'none' },
            skippedStyle: { display: 'none' },
            unreachableStyle: { display: 'none' },
            hostResults: {}
        };

        if (scope.jobData.plays[event.parent].firstTask === undefined || scope.jobData.plays[event.parent].firstTask === null) {
            scope.jobData.plays[event.parent].firstTask = event.id;
        }
        scope.jobData.plays[event.parent].taskCount++;

        SetActivePlay({ scope: scope });

        SetActiveTask({ scope: scope });

        UpdatePlayStatus({
            scope: scope,
            play_id: event.parent,
            failed: event.failed,
            changed: event.changed,
            modified: event.modified
        });
    };
}])

.factory('UpdateJobStatus', ['GetElapsed', 'Empty', 'JobIsFinished', function(GetElapsed, Empty, JobIsFinished) {
    return function(params) {
        var scope = params.scope,
            failed = params.failed,
            modified = params.modified,
            started =  params.started;

        if (failed && scope.job_status.status !== 'failed' && scope.job_status.status !== 'error' &&
            scope.job_status.status !== 'canceled') {
            scope.job_status.status = 'failed';
        }
        if (JobIsFinished(scope) && !Empty(modified)) {
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
            play;

        if (scope.jobData.plays[id] !== undefined) {
            play = scope.jobData.plays[id];
            if (failed) {
                play.status = 'failed';
                play.status_text = 'Failed';
            }
            else if (play.status !== 'changed' && play.status !== 'failed') {
                // once the status becomes 'changed' or 'failed' don't modify it
                if (no_hosts) {
                    play.status = 'no-matching-hosts';
                    play.status_text = 'No matching hosts';
                } else {
                    play.status = (changed) ? 'changed' : (failed) ? 'failed' : 'successful';
                    play.status_text = (changed) ? 'Changed' : (failed) ? 'Failed' : 'OK';
                }
            }
            play.taskCount = (play.taskCount > 0) ? play.taskCount : 1;  // set to a minimum of 1 to force drawing
            play.status_tip = "Event ID: " + play.id + "<br />Status: " + play.status_text;
            play.finished = modified;
            play.elapsed = GetElapsed({
                start: play.created,
                end: modified
            });
            //play.status_text = (status_text) ? status_text : play.status;
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
            play, task;

        // find the task in our hierarchy
        for (play in scope.jobData.plays) {
            if (scope.jobData.plays[play].tasks[id]) {
                task = scope.jobData.plays[play].tasks[id];
            }
        }

        if (task) {
            if (no_hosts){
                task.status = 'no-matching-hosts';
                task.status_text = 'No matching hosts';
            }
            else if (failed) {
                task.status = 'failed';
                task.status_text = 'Failed';
            }
            else if (task.status !== 'changed' && task.status !== 'failed') {
                // once the status becomes 'changed' or 'failed' don't modify it
                task.status = (failed) ? 'failed' : (changed) ? 'changed' : 'successful';
                task.status_text = (failed) ? 'Failed' : (changed) ? 'Changed' : 'OK';
            }
            task.status_tip = "Event ID: " + task.id + "<br />Status: " + task.status_text;
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
.factory('UpdateHostStatus', ['UpdateTaskStatus', 'AddHostResult', function(UpdateTaskStatus, AddHostResult) {
    return function(params) {
        var scope = params.scope,
            status = params.status,  // successful, changed, unreachable, failed, skipped
            name = params.name,
            event_id = params.id,
            host_id = params.host_id,
            task_id = params.task_id,
            modified = params.modified,
            created = params.created,
            msg = params.message,
            item = params.item,
            h, host;

        /*
        scope.host_summary.ok += (status === 'successful') ? 1 : 0;
        scope.host_summary.changed += (status === 'changed') ? 1 : 0;
        scope.host_summary.unreachable += (status === 'unreachable') ? 1 : 0;
        scope.host_summary.failed += (status === 'failed') ? 1 : 0;
        scope.host_summary.total  = scope.host_summary.ok + scope.host_summary.changed + scope.host_summary.unreachable +
            scope.host_summary.failed;
        */

        if (scope.jobData.hostSummaries[host_id] !== undefined) {
            scope.jobData.hostSummaries[host_id].ok += (status === 'successful') ? 1 : 0;
            scope.jobData.hostSummaries[host_id].changed += (status === 'changed') ? 1 : 0;
            scope.jobData.hostSummaries[host_id].unreachable += (status === 'unreachable') ? 1 : 0;
            scope.jobData.hostSummaries[host_id].failed += (status === 'failed') ? 1 : 0;
            if (status === 'failed' || status === 'unreachable') {
                scope.jobData.hostSummaries[host_id].status = 'failed';
            }
        }
        else {
            scope.jobData.hostSummaries[host_id] = {
                id: host_id,
                name: name,
                ok: (status === 'successful') ? 1 : 0,
                changed: (status === 'changed') ? 1 : 0,
                unreachable: (status === 'unreachable') ? 1 : 0,
                failed: (status === 'failed') ? 1 : 0,
                status: (status === 'failed' || status === 'unreachable') ? 'failed' : 'successful'
            };
        }

        scope.host_summary.ok = 0;
        scope.host_summary.changed = 0;
        scope.host_summary.unreachable = 0;
        scope.host_summary.failed = 0;
        for (h in scope.jobData.hostSummaries) {
            host = scope.jobData.hostSummaries[h];
            if (host.ok > 0 && host.failed === 0 && host.unreachable === 0 && host.changed === 0) {
                scope.host_summary.ok++;
            }
            if (host.changed > 0 && host.failed === 0 && host.unreachable === 0) {
                scope.host_summary.changed++;
            }
            if (host.failed > 0) {
                scope.host_summary.failed++;
            }
            if (host.unreachable > 0) {
                scope.host_summary.unreachable++;
            }
        }
        scope.host_summary.total = scope.host_summary.ok + scope.host_summary.changed + scope.host_summary.unreachable +
            scope.host_summary.failed;

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
            message: msg,
            item: item
        });
    };
}])

// Add a new host result
.factory('AddHostResult', ['SetTaskStyles', 'SetActivePlay', 'SetActiveTask', function(SetTaskStyles, SetActivePlay, SetActiveTask) {
    return function(params) {
        var scope = params.scope,
            task_id = params.task_id,
            host_id = params.host_id,
            event_id = params.event_id,
            status = params.status,
            created = params.created,
            name = params.name,
            msg = params.message,
            item = params.item,
            status_text = '',
            task, play, play_id;

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

        if (typeof item === "object") {
            item = JSON.stringify(item);
        }

        for (play in scope.jobData.plays) {
            for (task in scope.jobData.plays[play].tasks) {
                if (parseInt(task,10) === parseInt(task_id,10)) {
                    play_id = parseInt(play,10);
                }
            }
        }

        if (play_id) {
            scope.jobData.plays[play_id].tasks[task_id].hostResults[event_id] = {
                id: event_id,
                status: status,
                status_text: status_text,
                host_id: host_id,
                task_id: task_id,
                name: name,
                created: created,
                msg: msg,
                item: item
            };

            // increment the unreachable count on the play
            if (status === 'unreachable') {
                scope.jobData.plays[play_id].unreachableCount++;
            }

            // update the task status bar
            task = scope.jobData.plays[play_id].tasks[task_id];

            if (task_id === scope.jobData.plays[play_id].firstTask) {
                scope.jobData.plays[play_id].hostCount++;
                task.hostCount++;
            }

            task.reportedHosts += 1;
            task.failedCount += (status === 'failed') ? 1 : 0;
            task.changedCount += (status === 'changed') ? 1 : 0;
            task.successfulCount += (status === 'successful') ? 1 : 0;
            task.skippedCount += (status === 'skipped') ? 1 : 0;
            task.unreachableCount += (status === 'unreachable') ? 1 : 0;

            SetTaskStyles({
                task: task
            });

            SetActivePlay({ scope: scope });

            SetActiveTask({ scope: scope });
        }
    };
}])

.factory('SetTaskStyles', [ function() {
    return function(params) {
        var task = params.task,
            diff;

        task.missingCount = task.hostCount - (task.failedCount + task.changedCount + task.skippedCount + task.successfulCount + task.unreachableCount);
        task.missingPct = (task.hostCount > 0) ? Math.ceil((100 * (task.missingCount / task.hostCount))) : 0;
        task.failedPct = (task.hostCount > 0) ? Math.ceil((100 * (task.failedCount / task.hostCount))) : 0;
        task.changedPct = (task.hostCount > 0) ? Math.ceil((100 * (task.changedCount / task.hostCount))) : 0;
        task.skippedPct = (task.hostCount > 0) ? Math.ceil((100 * (task.skippedCount / task.hostCount))) : 0;
        task.successfulPct = (task.hostCount > 0) ? Math.ceil((100 * (task.successfulCount / task.hostCount))) : 0;
        task.unreachablePct = (task.hostCount > 0) ? Math.ceil((100 * (task.unreachableCount / task.hostCount))) : 0;

        // cap % at 100
        task.missingPct = (task.missingPct > 100) ? 100 : task.missingPct;
        task.failedPct = (task.failedPct > 100) ? 100 : task.failedPct;
        task.changedPct = (task.changedPct > 100) ? 100 : task.changedPct;
        task.skippedPct = (task.skippedPct  > 100) ? 100 : task.skippedPct;
        task.successfulPct = ( task.successfulPct > 100) ? 100 :  task.successfulPct;
        task.unreachablePct = (task.unreachablePct > 100) ? 100 : task.unreachablePct;

        diff = (task.failedPct + task.changedPct + task.skippedPct + task.successfulPct + task.unreachablePct + task.missingPct) - 100;
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
            else if (task.unreachablePct > diff) {
                task.unreachablePct = task.unreachablePct - diff;
            }
            else if (task.missingPct > diff) {
                task.missingPct = task.missingPct - diff;
            }
        }
        task.successfulStyle = (task.successfulPct > 0) ? { 'display': 'inline-block', 'width': task.successfulPct + "%" } : { 'display': 'none' };
        task.changedStyle = (task.changedPct > 0) ? { 'display': 'inline-block', 'width': task.changedPct + "%" } : { 'display': 'none' };
        task.skippedStyle = (task.skippedPct > 0) ? { 'display': 'inline-block', 'width': task.skippedPct + "%" } : { 'display': 'none' };
        task.failedStyle = (task.failedPct > 0) ? { 'display': 'inline-block', 'width': task.failedPct + "%" } : { 'display': 'none' };
        task.unreachableStyle = (task.unreachablePct > 0) ? { 'display': 'inline-block', 'width': task.unreachablePct + "%" } : { 'display': 'none' };
        task.missingStyle = (task.missingPct > 0) ? { 'display': 'inline-block', 'width': task.missingPct + "%" } : { 'display': 'none' };
    };
}])

.factory('LoadPlays', ['Rest', 'ProcessErrors', 'GetElapsed', 'SelectPlay', 'JobIsFinished',
    function(Rest, ProcessErrors, GetElapsed, SelectPlay, JobIsFinished) {
    return function(params) {
        var scope = params.scope,
            callback = params.callback,
            url;

        scope.plays = [];

        url = scope.job.url + 'job_plays/?page_size=' + scope.playsMaxRows + '&order_by=id';
        url += (scope.search_play_name) ? '&play__icontains=' + scope.search_play_name : '';
        url += (scope.search_play_status === 'failed') ? '&failed=true' : '';
        scope.playsLoading = true;
        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                scope.next_plays = data.next;
                data.results.forEach(function(event, idx) {
                    var status, status_text, start, end, elapsed;

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
                });

                // set the active task
                SelectPlay({
                    scope: scope,
                    id: (scope.plays.length > 0) ? scope.plays[0].id : null,
                    callback: callback
                });
                scope.playsLoading = false;
            })
            .error(function(data) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + '. GET returned: ' + status });
            });
    };
}])

// Call when the selected Play needs to change
.factory('SelectPlay', ['LoadTasks', function(LoadTasks) {
    return function(params) {
        var scope = params.scope,
            id = params.id,
            callback = params.callback;

        scope.selectedPlay = id;
        scope.plays.forEach(function(play, idx) {
            if (play.id === scope.selectedPlay) {
                scope.plays[idx].playActiveClass = 'active';
            }
            else {
                scope.plays[idx].playActiveClass = '';
            }
        });

        LoadTasks({
            scope: scope,
            callback: callback,
            clear: true
        });

    };
}])

.factory('LoadTasks', ['Rest', 'ProcessErrors', 'GetElapsed', 'SelectTask', 'SetTaskStyles', function(Rest, ProcessErrors, GetElapsed, SelectTask, SetTaskStyles) {
    return function(params) {
        var scope = params.scope,
            callback = params.callback,
            url, play;

        scope.tasks = [];
        scope.tasksMap = {};

        if (scope.selectedPlay) {
            url = scope.job.url + 'job_tasks/?event_id=' + scope.selectedPlay;
            url += (scope.search_task_name) ? '&task__icontains=' + scope.search_task_name : '';
            url += (scope.search_task_status === 'failed') ? '&failed=true' : '';
            url += '&page_size=' + scope.tasksMaxRows + '&order_by=id';

            scope.plays.every(function(p, idx) {
                if (p.id === scope.selectedPlay) {
                    play = scope.plays[idx];
                    return false;
                }
                return true;
            });

            scope.tasksLoading = true;

            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    scope.next_tasks = data.next;
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
                            scope.plays.every(function(play) {
                                if (play.id === scope.selectedPlay) {
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
                            hostCount: (event.host_count) ? event.host_count : 0,
                            reportedHosts: (event.reported_hosts) ? event.reported_hosts : 0,
                            successfulCount: (event.successful_count) ? event.successful_count : 0,
                            failedCount: (event.failed_count) ? event.failed_count : 0,
                            changedCount: (event.changed_count) ? event.changed_count : 0,
                            skippedCount: (event.skipped_count) ? event.skipped_count : 0,
                            unreachableCount: (event.unreachable_count) ? event.unreachable_count : 0,
                            taskActiveClass: ''
                        });

                        if (play.firstTask !== event.id) {
                            // this is not the first task
                            scope.tasks[scope.tasks.length - 1].hostCount = play.hostCount;
                        }

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

                    scope.tasksLoading = false;

                })
                .error(function(data) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
        else {
            SelectTask({
                scope: scope,
                id: null,
                callback: callback
            });
        }
    };
}])

// Call when the selected task needs to change
.factory('SelectTask', ['LoadHosts', function(LoadHosts) {
    return function(params) {
        var scope = params.scope,
            id = params.id,
            callback = params.callback;

        scope.selectedTask = id;
        scope.tasks.forEach(function(task, idx) {
            if (task.id === scope.selectedTask) {
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
            url;

        scope.hostResults = [];
        scope.hostResultsMap = {};

        if (scope.selectedTask) {
            // If we have a selected task, then get the list of hosts
            url = scope.job.related.job_events + '?parent=' + scope.selectedTask + '&';
            url += (scope.search_host_name) ? 'host__name__icontains=' + scope.search_host_name + '&' : '';
            url += (scope.search_host_status === 'failed') ? 'failed=true&' : '';
            url += 'event__startswith=runner&page_size=' + scope.hostResultsMaxRows + '&order_by=host__name';
            scope.hostResultsLoading = true;
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    scope.next_host_results = data.next;
                    data.results.forEach(function(event) {
                        var status, status_text, item, msg;
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
                                item = item.replace(/\"/g,'').replace(/:/g,': ').replace(/,/g,', ');
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
                            scope.hostResults.push({
                                id: event.id,
                                status: status,
                                status_text: status_text,
                                host_id: event.host,
                                task_id: event.parent,
                                name: event.event_data.host,
                                created: event.created,
                                msg: msg,
                                item: item
                            });
                        }
                    });

                    scope.hostResultsLoading = false;

                    if (callback) {
                        scope.$emit(callback);
                    }
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
            //$('#hosts-table-detail').mCustomScrollbar("update");
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
        url += (scope.search_host_summary_name) ? 'host_name__icontains=' + scope.search_host_summary_name + '&': '';
        url += (scope.search_host_summary_status === 'failed') ? 'failed=true&' : '';
        url += '&page_size=' + scope.hostSummariesMaxRows + '&order_by=host_name';

        scope.hosts = [];
        scope.hostSummariesLoading = true;

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
                    scope.hosts.push({
                        id: event.host,
                        name: name,
                        ok: event.ok,
                        changed: event.changed,
                        unreachable: event.dark,
                        failed: event.failures,
                        status: (event.failed) ? 'failed' : 'successful'
                    });
                });

                scope.hostSummariesLoading = false;

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
            if (!data.changed[host] && !data.dark[host] && !data.failures[host]) {
                scope.host_summary.ok += 1;
            }
        }
        scope.host_summary.changed = 0;
        for (host in data.changed) {
            if (!data.dark[host] && !data.failures[host]) {
                scope.host_summary.changed += 1;
            }
        }
        scope.host_summary.unreachable = 0;
        for (host in data.dark) {
            scope.host_summary.unreachable += 1;
        }
        scope.host_summary.failed = 0;
        for (host in data.failures) {
            scope.host_summary.failed += 1;
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
                color: '#FF0000'
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

.factory('DrawPlays', [function() {
    return function(params) {
        var scope = params.scope,
            idx = 0,
            result = [],
            newKeys = [],
            plays = JSON.parse(JSON.stringify(scope.jobData.plays)),
            filteredListX = [],
            filteredListA = [],
            filteredListB = [],
            key,
            keys;

        function listSort(a,b) {
            if (parseInt(a,10) < parseInt(b,10))
                return -1;
            if (parseInt(a,10) > parseInt(b,10))
                return 1;
            return 0;
        }

        // Only draw plays that are in the 'active' list
        for (key in plays) {
            if (plays[key].taskCount > 0) {
                filteredListX[key] = plays[key];
            }
        }
        if (scope.search_play_name) {
            for (key in plays) {
                if (filteredListX[key].name.indexOf(scope.search_play_name) > 0) {
                    filteredListA[key] = filteredListX[key];
                }
            }
        }
        else {
            filteredListA = filteredListX;
        }

        if (scope.search_play_status === 'failed') {
            for (key in filteredListA) {
                if (filteredListA[key].status === 'failed') {
                    filteredListB[key] = plays[key];
                }
            }
        }
        else {
            filteredListB = filteredListA;
        }

        keys = Object.keys(filteredListB);
        keys.sort(function(a,b) { return listSort(a,b); }).reverse();
        for (idx=0; idx < scope.playsMaxRows && idx < keys.length; idx++) {
            newKeys.push(keys[idx]);
        }
        newKeys.sort(function(a,b) { return listSort(a,b); });
        idx = 0;
        while (idx < newKeys.length) {
            result.push(filteredListB[newKeys[idx]]);
            idx++;
        }
        setTimeout( function() {
            scope.$apply( function() {
                scope.plays = result;
                scope.selectedPlay = scope.activePlay;
                if (scope.liveEventProcessing) {
                    $('#plays-table-detail').scrollTop($('#plays-table-detail').prop("scrollHeight"));
                }
            });
        });
    };
}])

.factory('DrawTasks', [ function() {
    return function(params) {
        var scope = params.scope,
            result = [],
            filteredListX = [],
            filteredListA = [],
            filteredListB = [],
            idx, key, keys, newKeys, tasks, t;

        function listSort(a,b) {
            if (parseInt(a,10) < parseInt(b,10))
                return -1;
            if (parseInt(a,10) > parseInt(b,10))
                return 1;
            return 0;
        }

        if (scope.activePlay && scope.jobData.plays[scope.activePlay]) {

            tasks = JSON.parse(JSON.stringify(scope.jobData.plays[scope.activePlay].tasks));

            // Only draw tasks that are in the 'active' list
            for (key in tasks) {
                t = tasks[key];
                if (t.reportedHosts > 0 || t.hostCount > 0 || t.successfulCount >0 || t.failedCount > 0 ||
                    t.changedCount > 0 || t.skippedCount > 0 || t.unreachableCount > 0) {
                    filteredListX[key] = tasks[key];
                }
            }

            if (scope.search_task_name) {
                for (key in filteredListX) {
                    if (filteredListX[key].name.indexOf(scope.search_task_name) > 0) {
                        filteredListA[key] = filteredListX[key];
                    }
                }
            }
            else {
                filteredListA = filteredListX;
            }

            if (scope.search_task_status === 'failed') {
                for (key in filteredListA) {
                    if (filteredListA[key].status === 'failed') {
                        filteredListB[key] = tasks[key];
                    }
                }
            }
            else {
                filteredListB = filteredListA;
            }

            keys = Object.keys(filteredListB);
            keys.sort(function(a,b) { return listSort(a,b); }).reverse();
            newKeys = [];
            for (idx=0; result.length < scope.tasksMaxRows && idx < keys.length; idx++) {
                newKeys.push(keys[idx]);
            }
            newKeys.sort(function(a,b) { return listSort(a,b); });
            idx = 0;
            while (idx < newKeys.length) {
                result.push(filteredListB[newKeys[idx]]);
                idx++;
            }
        }

        setTimeout( function() {
            scope.$apply( function() {
                scope.tasks = result;
                scope.selectedTask = scope.activeTask;
                if (scope.liveEventProcessing) {
                    $('#tasks-table-detail').scrollTop($('#tasks-table-detail').prop("scrollHeight"));
                }
            });
        });

    };
}])

.factory('DrawHostResults', [ function() {
    return function(params) {
        var scope = params.scope,
            result = [],
            filteredListA = [],
            filteredListB = [],
            idx = 0,
            hostResults,
            key,
            keys;

        if (scope.activePlay && scope.activeTask && scope.jobData.plays[scope.activePlay] &&
            scope.jobData.plays[scope.activePlay].tasks[scope.activeTask]) {

            hostResults = JSON.parse(JSON.stringify(scope.jobData.plays[scope.activePlay].tasks[scope.activeTask].hostResults));

            if (scope.search_host_name) {
                for (key in hostResults) {
                    if (hostResults[key].name.indexOf(scope.search_host_name) > 0) {
                        filteredListA[key] = hostResults[key];
                    }
                }
            }
            else {
                filteredListA = hostResults;
            }

            if (scope.search_host_status === 'failed' || scope.search_host_status === 'unreachable') {
                for (key in filteredListA) {
                    if (filteredListA[key].status === 'failed') {
                        filteredListB[key] = filteredListA[key];
                    }
                }
            }
            else {
                filteredListB = filteredListA;
            }

            keys = Object.keys(filteredListB);
            keys.sort(function(a,b) {
                if (filteredListB[a].name + filteredListB[a].item > filteredListB[b].name + filteredListB[b].item)
                    return -1;
                if (filteredListB[a].name + filteredListB[a].item < filteredListB[b].name + filteredListB[b].item)
                    return 1;
                // a must be equal to b
                return 0;
            });
            while (idx < keys.length && result.length < scope.hostResultsMaxRows) {
                result.unshift(filteredListB[keys[idx]]);
                idx++;
            }
        }

        setTimeout( function() {
            scope.$apply( function() {
                scope.hostResults = result;
                if (scope.liveEventProcessing) {
                    $('#hosts-table-detail').scrollTop($('#hosts-table-detail').prop("scrollHeight"));
                }
            });
        });

    };
}])

.factory('DrawHostSummaries', [ function() {
    return function(params) {
        var scope = params.scope,
            result = [],
            filteredListA = [],
            filteredListB = [],
            idx = 0,
            hostSummaries,
            key,
            keys = Object.keys(scope.jobData.hostSummaries);
        if (keys.length > 0) {
            hostSummaries = JSON.parse(JSON.stringify(scope.jobData.hostSummaries));
            if (scope.search_host_summary_name) {
                for (key in hostSummaries) {
                    if (hostSummaries[key].name.indexOf(scope.search_host_summary_name) > 0) {
                        filteredListA[key] = hostSummaries[key];
                    }
                }
            }
            else {
                filteredListA = hostSummaries;
            }

            if (scope.search_host_summary_status === 'failed') {
                for (key in filteredListA) {
                    if (filteredListA[key].status === 'failed' || filteredListA[key].status === 'unreachable') {
                        filteredListB[key] = filteredListA[key];
                    }
                }
            }
            else {
                filteredListB = filteredListA;
            }

            keys = Object.keys(filteredListB);

            keys.sort(function(a,b) {
                if (filteredListB[a].name > filteredListB[b].name)
                    return 1;
                if (filteredListB[a].name < filteredListB[b].name)
                    return -1;
                // a must be equal to b
                return 0;
            });

            while (idx < keys.length && result.length < scope.hostSummariesMaxRows) {
                result.push(filteredListB[keys[idx]]);
                idx++;
            }
        }
        setTimeout( function() {
            scope.$apply( function() {
                scope.hosts = result;
            });
        });
    };
}])

.factory('UpdateDOM', ['DrawPlays', 'DrawTasks', 'DrawHostResults', 'DrawHostSummaries', 'DrawGraph',
    function(DrawPlays, DrawTasks, DrawHostResults, DrawHostSummaries, DrawGraph) {
    return function(params) {
        var scope = params.scope;

        if (!scope.pauseLiveEvents) {
            DrawPlays({ scope: scope });
            DrawTasks({ scope: scope });
            DrawHostResults({ scope: scope });
        }

        DrawHostSummaries({ scope: scope });

        setTimeout(function() {
            scope.playsLoading = false;
            scope.tasksLoading = false;
            scope.hostResultsLoading = false;
            scope.LoadHostSummaries = false;
        },100);

        if (scope.host_summary.total > 0) {
            DrawGraph({ scope: scope, resize: true });
        }
    };
}]);
