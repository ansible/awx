/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/

export default [function(){
    var val = {};

    // the playbook_on_stats event returns the count data in a weird format.
    // format to what we need!
    var getCountsFromStatsEvent = function(event_data) {
        var hosts = {},
            hostsArr;

        // iterate over the event_data and populate an object with hosts
        // and their status data
        Object.keys(event_data).forEach(key => {
            // failed passes boolean not integer
            if (key === "failed") {
                // array of hosts from failed type
                hostsArr = Object.keys(event_data[key]);
                hostsArr.forEach(host => {
                    if (!hosts[host]) {
                        // host has not been added to hosts object
                        // add now
                        hosts[host] = {};
                    }

                    hosts[host][key] = event_data[key][host];
                });
            } else {
                // array of hosts from each type ("changed", "dark", etc.)
                hostsArr = Object.keys(event_data[key]);
                hostsArr.forEach(host => {
                    if (!hosts[host]) {
                        // host has not been added to hosts object
                        // add now
                        hosts[host] = {};
                    }

                    if (!hosts[host][key]) {
                        // host doesn't have key
                        hosts[host][key] = 0;
                    }
                    hosts[host][key] += event_data[key][host];
                });
            }
        });

        // use the hosts data populate above to get the count
        var count = {
            ok : _.filter(hosts, function(o){
                return !o.failures && !o.changed && o.ok > 0;
            }),
            skipped : _.filter(hosts, function(o){
                return o.skipped > 0;
            }),
            unreachable : _.filter(hosts, function(o){
                return o.dark > 0;
            }),
            failures : _.filter(hosts, function(o){
                return o.failed === true;
            }),
            changed : _.filter(hosts, function(o){
                return o.changed > 0;
            })
        };

        // turn the count into an actual count, rather than a list of host
        // names
        Object.keys(count).forEach(key => {
            count[key] = count[key].length;
        });

        return count;
    };

    // munge the raw event from the backend into the event_queue's format
    var mungeEvent = function(event) {
        var mungedEvent = {
            id: event.id,
            processed: false
        };
        if (event.event_name === 'playbook_on_start') {
            event.count = val.queue.count;
            mungedEvent.changes = ['count'];
        } else if (event.event_name === 'runner_on_ok' ||
            event.event_name === 'runner_on_async_ok') {
            val.queue.count.ok++;
            event.count = val.queue.count;
            mungedEvent.changes = ['count'];
        } else if (event.event_name === 'runner_on_skipped') {
            val.queue.count.skipped++;
            event.count = val.queue.count;
            mungedEvent.changes = ['count'];
        } else if (event.event_name === 'runner_on_unreachable') {
            val.queue.count.unreachable++;
            event.count = val.queue.count;
            mungedEvent.changes = ['count'];
        } else if (event.event_name === 'runner_on_error' ||
            event.event_name === 'runner_on_async_failed') {
            val.queue.count.failed++;
            event.count = val.queue.count;
            mungedEvent.changes = ['count'];
        } else if (event.event_name === 'playbook_on_stats') {
            // get the data for populating the host status bar
            val.queue.count = getCountsFromStatsEvent(event.event_data);
            event.count = val.queue.count;
            mungedEvent.changes = ['count'];
        }
        return mungedEvent;
    };

    val = {
        queue: {},
        // reinitializes the event queue value for the job results page
        initialize: function() {
            val.queue = {};

            // initialize the host status counts
            val.queue.count = {
                ok: 0,
                skipped: 0,
                unreachable: 0,
                failures: 0,
                changed: 0
            };
        },
        // populates the event queue
        populate: function(event) {
            var mungedEvent = mungeEvent(event);
            val.queue[event.id] = mungedEvent;

            return mungedEvent;
        },
        // the event has been processed in the view and should be marked as
        // completed in the queue
        markProcessed: function(event) {
            val.queue[event.id].processed = true;
        }
    };

    return val;
}];
