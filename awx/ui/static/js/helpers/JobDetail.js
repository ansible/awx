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

.factory('DigestEvents', ['UpdatePlayStatus', 'UpdateHostStatus', 'UpdatePlayChild', 'AddHostResult', 'SelectPlay', 'SelectTask',
    'GetHostCount', 'GetElapsed', 'UpdateTaskStatus',
function(UpdatePlayStatus, UpdateHostStatus, UpdatePlayChild, AddHostResult, SelectPlay, SelectTask, GetHostCount, GetElapsed,
    UpdateTaskStatus) {
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
                scope.plays.push({
                    id: event.id,
                    name: event.play,
                    created: event.created,
                    status: (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'none',
                    elapsed: '00:00:00',
                    children: []
                });
                SelectPlay({
                    scope: scope,
                    id: event.id
                });
            }
            if (event.event === 'playbook_on_setup') {
                hostCount = GetHostCount({
                    scope: scope,
                    play_id: event.parent
                });
                scope.tasks.push({
                    id: event.id,
                    name: event.event_display,
                    play_id: ( (event.parent) ? event.parent : scope.activePlay ),
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
                });
                UpdatePlayStatus({
                    scope: scope,
                    play_id: event.parent,
                    failed: event.failed,
                    changed: event.changed,
                    modified: event.modified
                });
                SelectTask({
                    scope: scope,
                    id: event.id
                });
            }
            if (event.event === 'playbook_on_no_hosts_matched') {
                UpdatePlayStatus({
                    scope: scope,
                    play_id: event.parent,
                    failed: true,
                    changed: false,
                    modified: event.modified
                });
            }
            if (event.event === 'playbook_on_task_start') {
                hostCount = GetHostCount({
                    scope: scope,
                    play_id: event.parent
                });
                scope.tasks.push({
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
                });
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
                SelectTask({
                    scope: scope,
                    id: event.id
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
                scope.liveEventsEnabled = true; // Show the stop button
                scope.liveEventToggleDisabled = true;  //Disable clicking on the button, the job is over
            }
        });
    };
}])

.factory('GetHostCount', function() {
    return function(params) {
        var scope = params.scope,
            play_id = params.play_id,
            tasks = [];
        // Get the known set of tasks for a given play
        if (scope.tasks.length > 0) {
            scope.tasks.forEach(function(task) {
                if (task.play_id === play_id) {
                    tasks.push(task);
                }
            });
            // sort by ascending event.id
            if (tasks.length > 0) {
                tasks.sort(function(a, b) {
                    return a.id - b.id;
                });
                return tasks[0].hostCount;
            }
        }
        return 0;
    };
})

.factory('FindFirstTaskofPlay', function() {
    return function(params) {
        var scope = params.scope,
            play_id = params.play_id,
            tasks = [];
        // Get the known set of tasks for a given play
        if (scope.tasks.length > 0) {
            scope.tasks.forEach(function(task) {
                if (task.play_id === play_id) {
                    tasks.push(task);
                }
            });
            // sort by ascending event.id
            if (tasks.length > 0) {
                tasks.sort(function(a, b) {
                    return a.id - b.id;
                });
                return tasks[0].id;
            }
        }
        return 0;
    };
})

.factory('MakeLastRowActive', [ function() {
    return function(params) {
        var scope = params.scope,
            list = params.list,
            field = params.field,
            set = params.set;
        list.forEach(function(row, idx) {
            list[idx][field] = '';
        });
        if (list.length > 0) {
            list[list.length - 1][field] = 'active';
            scope[set] = list[list.length - 1].id;
        }
    };
}])

.factory('UpdatePlayChild', [ function() {
    return function(params) {
        var scope = params.scope,
            id = params.id,
            play_id = params.play_id,
            failed = params.failed,
            name = params.name,
            found_child = false;
        scope.plays.every(function(play, i) {
            if (play.id === play_id) {
                scope.plays[i].children.every(function(child, j) {
                    if (child.id === id) {
                        scope.plays[i].children[j].status = (failed) ? 'failed' : 'successful';
                        found_child = true;
                        return false;
                    }
                    return true;
                });
                if (!found_child) {
                    scope.plays[i].children.push({
                        id: id,
                        name: name,
                        status: (failed) ? 'failed' : 'successful'
                    });
                }
                scope.plays[i].status = (failed) ? 'failed' : 'successful';
                return false;
            }
            return true;
        });
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
            no_hosts = params.no_hosts;
        scope.plays.every(function(play,idx) {
            if (play.id === id) {
                if (failed) {
                    scope.plays[idx].status = 'failed';
                }
                else if (play.status !== 'changed' && play.status !== 'failed') {
                    // once the status becomes 'changed' or 'failed' don't modify it
                    if (no_hosts) {
                        scope.plays[idx].status = 'no-matching-hosts';
                    }
                    else {
                        scope.plays[idx].status = (changed) ? 'changed' : (failed) ? 'failed' : 'successful';
                    }
                }
                scope.plays[idx].finished = modified;
                scope.plays[idx].elapsed = GetElapsed({
                    start: play.created,
                    end: modified
                });
                UpdateJobStatus({
                    scope: scope,
                    failed: null,
                    modified: modified
                });
                return false;
            }
            return true;
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
            no_hosts = params.no_hosts;
        scope.tasks.every(function (task, i) {
            if (task.id === id) {
                if (no_hosts){
                    scope.tasks[i].status = 'no-matching-hosts';
                }
                else if (failed) {
                    scope.tasks[i].status = 'failed';
                }
                else if (task.status !== 'changed' && task.status !== 'failed') {
                    // once the status becomes 'changed' or 'failed' don't modify it
                    scope.tasks[i].status = (failed) ? 'failed' : (changed) ? 'changed' : 'successful';
                }
                scope.tasks[i].finished = params.modified;
                scope.tasks[i].elapsed = GetElapsed({
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
                return false;
            }
            return true;
        });
    };
}])

// Update host summary totals and update the task
.factory('UpdateHostStatus', ['UpdateTaskStatus', 'AddHostResult', function(UpdateTaskStatus, AddHostResult) {
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
            host_found = false;

        scope.hosts.every(function(host, i) {
            if (host.id === host_id) {
                scope.hosts[i].ok += (status === 'successful') ? 1 : 0;
                scope.hosts[i].changed += (status === 'changed') ? 1 : 0;
                scope.hosts[i].unreachable += (status === 'unreachable') ? 1 : 0;
                scope.hosts[i].failed += (status === 'failed') ? 1 : 0;
                host_found = true;
                return false;
            }
            return true;
        });

        if (!host_found) {
            if (scope.hosts.length < 10 || name > scope.hosts[0].name) {
                // This is a new host we want added to the list 
                scope.hosts.push({
                    id: host_id,
                    name: name,
                    ok: (status === 'successful') ? 1 : 0,
                    changed: (status === 'changed') ? 1 : 0,
                    unreachable: (status === 'unreachable') ? 1 : 0,
                    failed: (status === 'failed') ? 1 : 0
                });
                scope.hosts.sort(function(a,b) {
                    if (a.name < b.name) {
                        return -1;
                    }
                    if (a.name > b.name) {
                        return 1;
                    }
                    return 0;
                });
                // Only keep 10 hosts
                if (scope.hosts.length > scope.hostSummaryTableRows) {
                    scope.hosts.splice(0,1);
                }
                $('#tasks-table-detail').mCustomScrollbar("update");
                setTimeout( function() {
                    scope.auto_scroll = true;
                    $('#hosts-summary-table').mCustomScrollbar("scrollTo", "bottom");
                }, 700);
            }
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
            play_id, first,
            tmp = [];

        // Remove any rows not related to the current task
        scope.hostResults.forEach(function(result, idx) {
            if (result.task_id !== task_id) {
                tmp.push(idx);
            }
        });
        tmp.forEach(function(row) {
            scope.hostResults.splice(row, 1);
        });

        // Sort
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
        if (scope.hostResults.length === scope.hostTableRows) {
            scope.hostResults.splice(0,1);
        }

        // Add the new row
        scope.hostResults.push({
            id: event_id,
            status: status,
            host_id: host_id,
            task_id: task_id,
            name: name,
            created: created,
            msg: msg
        });

        // Sort one more time
        scope.hostResults.sort(function(a,b) {
            if (a.name < b.name) {
                return -1;
            }
            if (a.name > b.name) {
                return 1;
            }
            return 0;
        });
        scope.tasks.every(function(task) {
            if (task.id === task_id) {
                play_id = task.play_id;
                return false;
            }
            return true;
        });

        first = FindFirstTaskofPlay({
            scope: scope,
            play_id: play_id
        });

        scope.tasks.every(function(task, idx) {
            var diff;
            if (task.id === task_id) {
                if (task.id === first) {
                    scope.tasks[idx].hostCount += 1;
                }
                scope.tasks[idx].reportedHosts++;
                scope.tasks[idx].failedCount += (status === 'failed' || status === 'unreachable') ? 1 : 0;
                scope.tasks[idx].changedCount += (status === 'changed') ? 1 : 0;
                scope.tasks[idx].successfulCount += (status === 'successful') ? 1 : 0;
                scope.tasks[idx].skippedCount += (status === 'skipped') ? 1 : 0;

                scope.tasks[idx].failedPct = (scope.tasks[idx].hostCount > 0) ? Math.ceil((100 * (scope.tasks[idx].failedCount / scope.tasks[idx].hostCount))) : 0;
                scope.tasks[idx].changedPct = (scope.tasks[idx].hostCount > 0) ? Math.ceil((100 * (scope.tasks[idx].changedCount / scope.tasks[idx].hostCount))) : 0;
                scope.tasks[idx].skippedPct = (scope.tasks[idx].hostCount > 0) ? Math.ceil((100 * (scope.tasks[idx].skippedCount / scope.tasks[idx].hostCount))) : 0;
                scope.tasks[idx].successfulPct = (scope.tasks[idx].hostCount > 0) ? Math.ceil((100 * (scope.tasks[idx].successfulCount / scope.tasks[idx].hostCount))) : 0;

                diff = (scope.tasks[idx].failedPct + scope.tasks[idx].changedPct + scope.tasks[idx].skippedPct + scope.tasks[idx].successfulPct) - 100;
                if (diff > 0) {
                    if (scope.tasks[idx].failedPct > diff) {
                        scope.tasks[idx].failedPct  = scope.tasks[idx].failedPct - diff;
                    }
                    else if (scope.tasks[idx].changedPct > diff) {
                        scope.tasks[idx].changedPct = scope.tasks[idx].changedPct - diff;
                    }
                    else if (scope.tasks[idx].skippedPct > diff) {
                        scope.tasks[idx].skippedPct = scope.tasks[idx].skippedPct - diff;
                    }
                    else if (scope.tasks[idx].successfulPct > diff) {
                        scope.tasks[idx].successfulPct = scope.tasks[idx].successfulPct - diff;
                    }
                }
                scope.tasks[idx].successfulStyle = (scope.tasks[idx].successfulPct > 0) ? { display: 'inline-block', width: scope.tasks[idx].successfulPct + '%' } : { display: 'none' };
                scope.tasks[idx].changedStyle = (scope.tasks[idx].changedPct > 0) ? { display: 'inline-block', width: scope.tasks[idx].changedPct + '%' } : { display: 'none' };
                scope.tasks[idx].skippedStyle = (scope.tasks[idx].skippedPct > 0) ? { display: 'inline-block', width: scope.tasks[idx].skippedPct + '%' } : { display: 'none' };
                scope.tasks[idx].failedStyle = (scope.tasks[idx].failedPct > 0) ? { display: 'inline-block', width: scope.tasks[idx].failedPct + '%' } : { display: 'none' };
                $('#' + task.id + '-' + task.play_id + '-' + 'successful-bar').css(scope.tasks[idx].successfulStyle);
                $('#' + task.id + '-' + task.play_id + '-' + 'changed-bar').css(scope.tasks[idx].changedStyle);
                $('#' + task.id + '-' + task.play_id + '-' + 'skipped-bar').css(scope.tasks[idx].skippedStyle);
                $('#' + task.id + '-' + task.play_id + '-' + 'failed-bar').css(scope.tasks[idx].failedStyle);
                return false;
            }
            return true;
        });
    };
}])

.factory('SelectPlay', ['SelectTask', function(SelectTask) {
    return function(params) {
        var scope = params.scope,
            id = params.id,
            max_task_id = 0;
        scope.plays.forEach(function(play, idx) {
            if (play.id === id) {
                scope.plays[idx].playActiveClass = 'active';
                scope.activePlay = id;
                scope.activePlayName = play.name;
            }
            else {
                scope.plays[idx].playActiveClass = '';
            }
        });
        
        // Select the last task
        scope.tasks.forEach(function(task) {
            if (task.play_id === scope.activePlay && task.id > max_task_id) {
                max_task_id = task.id;
            }
        });
        scope.activeTask = max_task_id;
        SelectTask({
            scope: scope,
            id: max_task_id
        });
    };
}])

.factory('SelectTask', ['SelectHost', 'GetBasePath', '$routeParams', 'Rest', 'ProcessErrors', 'Wait',
    function(SelectHost, GetBasePath, $routeParams, Rest, ProcessErrors, Wait) {
    return function(params) {
        var scope = params.scope,
            id = params.id,
            callback = params.callback,
            url;
        
        scope.tasks.forEach(function(task, idx) {
            if (task.id === id) {
                scope.tasks[idx].taskActiveClass = 'active';
                scope.activeTask = id;
                scope.activeTaskName = task.name;
            }
            else {
                scope.tasks[idx].taskActiveClass = '';
            }
        });
        
        if (callback) {
            callback();
        }
        
        $('#tasks-table-detail').mCustomScrollbar("update");
        setTimeout( function() {
            scope.auto_scroll = true;
            $('#tasks-table-detail').mCustomScrollbar("scrollTo", "bottom");
        }, 700);
        
        // Get current list of hosts from the API

        // is the job done? if so, only select hosts for the last task?

        Wait('start');
        scope.hostResults = [];
        url = GetBasePath('jobs') + $routeParams.id + '/job_events/?parent=' + id + '&';
        url += (scope.task_host_name) ? 'host__name__icontains=' + scope.task_host_name + '&' : '';
        url += 'host__isnull=false&page_size=' + scope.hostTableRows + '&order_by=host__name';
        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                data.results.forEach(function(row) {
                    scope.hostResults.push({
                        id: row.id,
                        status: ( (row.failed) ? 'failed' : (row.changed) ? 'changed' : 'successful' ),
                        host_id: row.host,
                        task_id: row.parent,
                        name: row.event_data.host,
                        created: row.created,
                        msg: ( (row.event_data && row.event_data.res) ? row.event_data.res.msg : '' )
                    });
                });
                Wait('stop');
                SelectHost({ scope: scope });
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

.factory('GetHostSummary', [ function() {

}])

.factory('DrawGraph', [ function() {
    /*var salesData=[
        {label:"OK", color:"#9ED89E"},
        {label:"Changed", color:"#DC3912"},
        {label:"Failed", color:"#DA4D49;"},
        {label:"Skipped", color:"#D4D4D4"},
        {label:"Unreachable", color:""}
    ];*/
}]);











