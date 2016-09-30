/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/

export default ['jobResultsService', function(jobResultsService){
    var val = {};

    // Get the count of the last event
    var getPreviousCount = function(counter) {
        // get the ids of all the queue
        var counters = Object.keys(val.queue).map(counter => parseInt(counter));

        // iterate backwards to find the last count
        while(counters.indexOf(counter - 1) > -1) {
            counter = counter - 1;
            if (val.queue[counter].count) {
                // need to create a new copy of count when returning
                // so that it is accurate for the particular event
                return _.clone(val.queue[counter].count);
            }
        }

        // no count initialized
        return {
            ok: 0,
            skipped: 0,
            unreachable: 0,
            failures: 0,
            changed: 0
        };
    };

    // munge the raw event from the backend into the event_queue's format
    var mungeEvent = function(event) {
        var mungedEvent = {
            counter: event.counter,
            id: event.id,
            processed: false,
            name: event.event_name
        };

        if (event.event_name === 'playbook_on_start') {
            // sets count initially so this is a change
            mungedEvent.count = getPreviousCount(mungedEvent.counter);
            mungedEvent.changes = ['count'];
        } else if (event.event_name === 'runner_on_ok' ||
            event.event_name === 'runner_on_async_ok') {
            mungedEvent.count = getPreviousCount(mungedEvent.counter);
            mungedEvent.count.ok++;
            mungedEvent.changes = ['count'];
        } else if (event.event_name === 'runner_on_skipped') {
            mungedEvent.count = getPreviousCount(mungedEvent.counter);
            mungedEvent.count.skipped++;
            mungedEvent.changes = ['count'];
        } else if (event.event_name === 'runner_on_unreachable') {
            mungedEvent.count = getPreviousCount(mungedEvent.counter);
            mungedEvent.count.unreachable++;
            mungedEvent.changes = ['count'];
        } else if (event.event_name === 'runner_on_error' ||
            event.event_name === 'runner_on_async_failed') {
            mungedEvent.count = getPreviousCount(mungedEvent.counter);
            mungedEvent.count.failed++;
            mungedEvent.changes = ['count'];
        } else if (event.event_name === 'playbook_on_stats') {
            // get the data for populating the host status bar
            mungedEvent.count = jobResultsService
                .getCountsFromStatsEvent(event.event_data);
            mungedEvent.changes = ['count', 'countFinished'];
        }
        return mungedEvent;
    };

    val = {
        queue: {},
        // reinitializes the event queue value for the job results page
        initialize: function() {
            val.queue = {};
        },
        // populates the event queue
        populate: function(event) {
            // don't populate the event if it's already been added either
            // by rest or by websocket event
            if (!val.queue[event.counter]) {
                var mungedEvent = mungeEvent(event);
                val.queue[mungedEvent.counter] = mungedEvent;

                return mungedEvent;
            }
        },
        // the event has been processed in the view and should be marked as
        // completed in the queue
        markProcessed: function(event) {
            val.queue[event.counter].processed = true;
        }
    };

    return val;
}];
