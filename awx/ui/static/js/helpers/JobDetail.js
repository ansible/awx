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

.factory('DigestEvents', ['UpdatePlayStatus', 'UpdatePlayNoHostsMatched', 'UpdateHostStatus', 'UpdatePlayChild', 'AddHostResult',
function(UpdatePlayStatus, UpdatePlayNoHostsMatched, UpdateHostStatus, UpdatePlayChild, AddHostResult) {
    return function(params) {
        var scope = params.scope,
            events = params.events;
        events.forEach(function(event) {
            if (event.event === 'playbook_on_play_start') {
                scope.plays.push({
                    id: event.id,
                    name: event.play,
                    status: (event.failed) ? 'failed' : 'successful',
                    children: []
                });
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
                    failed: event.failed
                });
            }
            if (event.event === 'playbook_on_task_start') {
                scope.tasks.push({
                    id: event.id,
                    name: event.task,
                    play_id: event.parent,
                    status: (event.failed) ? 'failed' : 'successful'
                });
                UpdatePlayStatus({
                    scope: scope,
                    play_id: event.parent,
                    failed: event.failed
                });
            }
            if (event.event === 'playbook_on_no_hosts_matched') {
                UpdatePlayNoHostsMatched({ scope: scope, play_id: event.parent });
            }
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
            id = params.play_id;
        scope.plays.every(function(play,idx) {
            if (play.id === id) {
                scope.plays[idx].status = (failed) ? 'failed' : 'successful';
                return false;
            }
            return true;
        });
    };
}])

.factory('UpdateTaskStatus', [ function() {
    return function(params) {
        var scope = params.scope,
            task_id = params.task_id,
            failed = params.failed;
        scope.tasks.every(function (task, i) {
            if (task.id === task_id) {
                scope.tasks[i].status = (failed) ? 'failed' : 'successful';
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

        // Mark task failed
        if (status === 'failed') {
            UpdateTaskStatus({
                scope: scope,
                task_id: task_id,
                failed: true
            });
        }
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
            play_name: play_name,
            task_name : task_name,
            module_name: module_name,
            module_args: module_args,
            results: results,
            rc: rc
        });
    };
}]);



