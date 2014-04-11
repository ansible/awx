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

.factory('DigestEvents', ['UpdatePlayStatus', 'UpdatePlayNoHostsMatched', function(UpdatePlayStatus, UpdatePlayNoHostsMatched) {
    return function(params) {
        var scope = params.scope,
            events = params.events;
        events.forEach(function(event) {
            if (event.event === 'playbook_on_play_start') {
                scope.plays.push({
                    id: event.id,
                    name: event.play,
                    status: (event.failed) ? 'failed' : 'successful'
                });
            }
            if (event.event === 'playbook_on_task_start') {
                scope.tasks.push({
                    id: event.id,
                    name: event.task,
                    play_id: event.parent,
                    status: (event.failed) ? 'failed' : 'successful'
                });
                UpdatePlayStatus({ scope: scope, play_id: event.parent, status: event.status });
            }
            if (event.event === 'playbook_on_no_hosts_matched') {
                UpdatePlayNoHostsMatched({ scope: scope, play_id: event.parent });
            }
            if (event.event === 'runner_on_failed') {

            }
            if (event.event === 'playbook_on_stats') {

            }

        });
    };
}])

// Update the status of a play
.factory('UpdatePlayStatus', [ function() {
    return function(params) {
        var scope = params.scope,
            status = params.status,
            id = params.play_id;
        scope.plays.every(function(play,idx) {
            if (play.id === id) {
                scope.plays[idx].status = (status) ? 'failed' : 'successful';
                return false;
            }
            return true;
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
}]);



