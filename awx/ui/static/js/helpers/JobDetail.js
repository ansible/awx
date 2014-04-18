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

.factory('DigestEvents', ['UpdatePlayStatus', 'UpdatePlayNoHostsMatched', 'UpdateHostStatus', 'UpdatePlayChild', 'AddHostResult', 'SelectPlay', 'SelectTask',
function(UpdatePlayStatus, UpdatePlayNoHostsMatched, UpdateHostStatus, UpdatePlayChild, AddHostResult, SelectPlay, SelectTask) {
    return function(params) {
        
        var scope = params.scope,
            events = params.events;
        
        events.forEach(function(event) {
            var hostCount;
            if (event.event === 'playbook_on_play_start') {
                scope.plays.push({
                    id: event.id,
                    name: event.play,
                    status: (event.changed) ? 'changed' : (event.failed) ? 'failed' : 'none',
                    children: []
                });
                SelectPlay({
                    scope: scope,
                    id: event.id
                });
            }
            if (event.event === 'playbook_on_setup') {
                hostCount = (scope.tasks.length > 0) ? scope.tasks[scope.tasks.length - 1].hostCount : 0;
                scope.tasks.push({
                    id: event.id,
                    name: event.event_display,
                    play_id: event.parent,
                    status: (event.failed) ? 'failed' : 'successful',
                    created: event.created,
                    hostCount: hostCount,
                    failedCount: 0,
                    changedCount: 0,
                    successfulCount: 0,
                    skippedCount: 0
                });
                UpdatePlayStatus({
                    scope: scope,
                    play_id: event.parent,
                    failed: event.failed,
                    changed: event.changed
                });
                SelectTask({
                    scope: scope,
                    id: event.id
                });
            }
            if (event.event === 'playbook_on_task_start') {
                hostCount = (scope.tasks.length > 0) ? scope.tasks[scope.tasks.length - 1].hostCount : 0;
                scope.tasks.push({
                    id: event.id,
                    name: event.task,
                    play_id: event.parent,
                    status: ( (event.changed) ? 'changed' : (event.failed) ? 'failed' : 'successful' ),
                    role: event.role,
                    created: event.created,
                    hostCount: hostCount,
                    failedCount: 0,
                    changedCount: 0,
                    successfulCount: 0,
                    skippedCount: 0
                });
                if (event.role) {
                    scope.hasRoles = true;
                }
                UpdatePlayStatus({
                    scope: scope,
                    play_id: event.parent,
                    failed: event.failed,
                    changed: event.changed
                });
                SelectTask({
                    scope: scope,
                    id: event.id
                });
            }
            /*if (event.event === 'playbook_on_no_hosts_matched') {
                UpdatePlayNoHostsMatched({ scope: scope, play_id: event.parent });
            }*/
    
            if (event.event === 'runner_on_unreachable') {
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: 'unreachable',
                    event_id: event.id
                });

            }
            if (event.event === 'runner_on_error') {
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: 'failed',
                    event_id: event.id
                });
            }
            if (event.event === 'runner_on_skipped') {
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: 'skipped',
                    event_id: event.id
                });
            }
            if (event.event === 'runner_on_ok') {
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host,
                    task_id: event.parent,
                    status: (event.changed) ? 'changed' : 'ok',
                    event_id: event.id
                });
            }
            if (event.event === 'playbook_on_stats') {

            }
        });
    };
}])

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

// Update the status of a play
.factory('UpdatePlayStatus', [ function() {
    return function(params) {
        var scope = params.scope,
            failed = params.failed,
            changed = params.changed,
            id = params.play_id;
        scope.plays.every(function(play,idx) {
            if (play.id === id) {
                scope.plays[idx].status = (changed) ? 'changed' : (failed) ? 'failed' : 'successful';
                return false;
            }
            return true;
        });
    };
}])

.factory('UpdateTaskStatus', ['UpdatePlayStatus', function(UpdatePlayStatus) {
    return function(params) {
        var scope = params.scope,
            failed = params.failed,
            changed = params.changed,
            id = params.task_id;
        scope.tasks.every(function (task, i) {
            if (task.id === id) {
                scope.tasks[i].status = (changed) ? 'changed' : (failed) ? 'failed' : 'successful';
                UpdatePlayStatus({
                    scope: scope,
                    failed: failed,
                    changed: changed,
                    play_id: task.play_id
                });
            }
        });
    };
}])

.factory('UpdatePlayNoHostsMatched', [ function() {
    return function(params) {
        var scope = params.scope,
            id = params.play_id;
        scope.plays.every(function(play,idx) {
            if (play.id === id) {
                scope.plays[idx].status = 'none';
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
            status = params.status,  // ok, changed, unreachable, failed
            name = params.name,
            event_id = params.event_id,
            host_id = params.host_id,
            task_id = params.task_id,
            host_found = false;

        scope.hosts.every(function(host, i) {
            if (host.id === host_id) {
                scope.hosts[i].ok += (status === 'ok' || status === 'changed') ? 1 : 0;
                scope.hosts[i].changed += (status === 'changed') ? 1 : 0;
                scope.hosts[i].unreachable += (status === 'unreachable') ? 1 : 0;
                scope.hosts[i].failed += (status === 'failed') ? 1 : 0;
                host_found = true;
                return false;
            }
            return true;
        });

        if (!host_found) {
            scope.hosts.push({
                id: host_id,
                name: name,
                ok: (status === 'ok' || status === 'changed') ? 1 : 0,
                changed: (status === 'changed') ? 1 : 0,
                unreachable: (status === 'unreachable') ? 1 : 0,
                failed: (status === 'failed') ? 1 : 0
            });
        }

        UpdateTaskStatus({
            scope: scope,
            task_id: task_id,
            failed: (status === 'failed' || status === 'unreachable') ? true :false,
            changed: (status === 'changed') ? true : false
        });

        AddHostResult({
            scope: scope,
            task_id: task_id,
            host_id: host_id,
            event_id: event_id
        });
    };
}])

// Add a new host result
.factory('AddHostResult', [ function() {
    return function(params) {
        var scope = params.scope,
            task_id = params.task_id,
            host_id = params.host_id,
            event_id = params.event_id,
            status = params.status;

        status = (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful';
        host_id = event.host;

        scope.hostResults.push({
            id: event_id,
            status: status,
            host_id: host_id,
            task_id: event.parent
        });

        scope.tasks.forEach(function(task, idx) {
            if (task.id === task_id) {
                scope.tasks[idx].hostCount += (idx === 0) ? 1 : 0;  // we only need to count hosts for the first task in a play
                scope.tasks[idx].failedCount += (status === 'failed' || status === 'unreachable') ? 1 : 0;
                scope.tasks[idx].changedCount += (status === 'changed') ? 1 : 0;
                scope.tasks[idx].successfulCount += (status === 'successful' || status === 'changed') ? 1 : 0;
                scope.tasks[idx].skippedCount += (status === 'skipped') ? 1 : 0;
                scope.tasks[idx].failedPct = 100 * Math.round(scope.tasks[idx].failedCount / scope.tasks[idx].hostCount);
                scope.tasks[idx].changedPct = 100 * (scope.tasks[idx].successfulCount) ? Math.round(scope.tasks[idx].changedCount / scope.tasks[idx].successfulCount) : 0;
                scope.tasks[idx].skippedPct = 100 * Math.round(scope.tasks[idx].skippedCount / scope.tasks[idx].hostCount);
                scope.tasks[idx].successfulPct = 100 * Math.round(scope.tasks[idx].successfulCount / scope.tasks[idx].hostCount);
            }
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
            id: max_task_id,
            callback: function() {
                // Scroll the task table all the way to the bottom, revealing the last row
                setTimeout(function() {
                    var original_height = $('#task-table-body').css('height'),
                        table_height;
                    $('#task-table-body').css('height', 'auto');
                    table_height = $('#task-table-body').height();
                    $('#task-table-body').css('height', original_height);
                    $('#task-table-body').scrollTop(table_height);
                }, 300);
            }
        });
    };
}])

.factory('SelectTask', ['SelectHost', function(SelectHost) {
    return function(params) {
        var scope = params.scope,
            id = params.id,
            callback = params.callback;
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
        SelectHost();
    };
}])

.factory('SelectHost', [ function() {
    return function() {
        setTimeout(function() {
            var inner_height = $('#host_details .job-detail-table').height();
            $('#host_details').scrollTop(inner_height);
        }, 100);
    };
}]);











