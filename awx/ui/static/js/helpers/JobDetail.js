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

.factory('DigestEvents', ['UpdatePlayStatus', 'UpdatePlayNoHostsMatched', 'UpdateHostStatus', 'UpdatePlayChild', 'AddHostResult', 'MakeLastRowActive',
function(UpdatePlayStatus, UpdatePlayNoHostsMatched, UpdateHostStatus, UpdatePlayChild, AddHostResult, MakeLastRowActive) {
    return function(params) {
        var scope = params.scope,
            events = params.events;
        events.forEach(function(event) {
            if (event.event === 'playbook_on_play_start') {
                scope.plays.push({
                    id: event.id,
                    name: event.play,
                    status: (event.changed) ? 'changed' : (event.failed) ? 'failed' : 'none',
                    children: []
                });
                scope.activePlay = event.id;
                MakeLastRowActive({ scope: scope, list: scope.plays, field: 'playActiveClass', set: 'activePlay' });
            }
            if (event.event === 'playbook_on_setup') {
                scope.tasks.push({
                    id: event.id,
                    name: event.event_display,
                    play_id: event.parent,
                    status: (event.failed) ? 'failed' : 'successful'
                });
                UpdatePlayStatus({
                    scope: scope,
                    play_id: event.parent,
                    failed: event.failed,
                    changed: event.changed
                });
            }
            if (event.event === 'playbook_on_task_start') {
                scope.tasks.push({
                    id: event.id,
                    name: event.task,
                    play_id: event.parent,
                    status: (event.changed) ? 'changed' : (event.failed) ? 'failed' : 'successful'
                });
                UpdatePlayStatus({
                    scope: scope,
                    play_id: event.parent,
                    failed: event.failed,
                    changed: event.changed
                });
                MakeLastRowActive({ scope: scope, list: scope.tasks, field: 'taskActiveClass', set: 'activeTask' });
            }
            /*if (event.event === 'playbook_on_no_hosts_matched') {
                UpdatePlayNoHostsMatched({ scope: scope, play_id: event.parent });
            }*/
            if (event.event === 'runner_on_failed') {

            }
            if (event.event === 'runner_on_ok') {
                UpdateHostStatus({
                    scope: scope,
                    name: event.event_data.host,
                    host_id: event.host_id,
                    task_id: event.parent,
                    status: (event.changed) ? 'changed' : 'ok',
                    results: (event.res && event.res.results) ? event.res.results : ''
                });
                AddHostResult({
                    scope: scope,
                    event: event
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
                scope.plays[idx].status = (changed) ? 'changed' : (failed) ? 'failed' : 'none';
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
                    play_id: task.parent
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

// Update or add a new host
.factory('UpdateHostStatus', ['UpdateTaskStatus', function(UpdateTaskStatus) {
    return function(params) {
        var scope = params.scope,
            status = params.status,  // ok, changed, unreachable, failed
            name = params.name,
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
    };
}])

// Add a new host result
.factory('AddHostResult', ['Empty', function(Empty) {
    return function(params) {
        var scope = params.scope,
            event = params.event,
            id, status, host_id, play_name, task_name, module_name, module_args,
            results, rc;

        id = event.id;
        status = (event.failed) ? 'failed' : (event.changed) ? 'changed' : 'successful';
        host_id = event.host;
        play_name = event.play;
        task_name = event.task;
        if (event.event_data.res && event.event_data.res.invocation) {
            module_name = event.event_data.res.invocation.module_name;
            module_args = event.event_data.res.invocation.module_args;
        }
        else {
            module_name = '';
            module_args = '';
        }
        if (event.event_data.res && event.event_data.res.results) {
            results = '';
            event.event_data.res.results.forEach(function(row) {
                results += row;
            });
        }
        rc = (event.event_data.res && !Empty(event.event_data.res.rc)) ? event.event_data.res.rc : '';
        scope.hostResults.push({
            id: id,
            status: status,
            host_id: host_id,
            task_id: event.parent,
            task_name: task_name,
            host_name: event.event_data.host,
            module_name: module_name,
            module_args: module_args,
            results: results,
            rc: rc
        });
    };
}])

.factory('SelectPlay', [ function() {
    return function(params) {
        var scope = params.scope,
            id = params.id;
        scope.plays.forEach(function(play, idx) {
            if (play.id === id) {
                scope.plays[idx].playActiveClass = 'active';
            }
            else {
                scope.plays[idx].playActiveClass = '';
            }
        });
        scope.activePlay = id;
    };
}])

.factory('SelectTask', [ function() {
    return function(params) {
        var scope = params.scope,
            id = params.id;
        scope.tasks.forEach(function(task, idx) {
            if (task.id === id) {
                scope.tasks[idx].taskActiveClass = 'active';
            }
            else {
                scope.tasks[idx].taskActiveClass = '';
            }
        });
        scope.activeTask = id;
    };
}]);
