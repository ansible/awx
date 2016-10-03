/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/

export default ['jobResultsService', '$q', function(jobResultsService, $q){
    var val = {};

    // Get the count of the last event
    var getPreviousCount = function(counter) {
        var previousCount = $q.defer();

        // iteratively find the last count
        var findCount = function(counter) {
            if (counter === 0) {
                // if counter is 0, no count has been initialized
                // initialize one!
                previousCount.resolve({
                    ok: 0,
                    skipped: 0,
                    unreachable: 0,
                    failures: 0,
                    changed: 0
                });
            } else if (val.queue[counter] && val.queue[counter].count) {
                // this event has a count, resolve!
                previousCount.resolve(_.clone(val.queue[counter].count));
            } else {
                // this event doesn't have a count, decrement to the
                // previous event and check it
                findCount(counter - 1);
            }
        };

        if (val.queue[counter - 1]) {
            // if the previous event has been resolved, start the iterative
            // get previous count process
            findCount(counter - 1);
        } else if (val.populateDefers[counter - 1]){
            // if the previous event has not been resolved, wait for it to
            // be and then start the iterative get previous count process
            val.populateDefers[counter - 1].promise.then(function() {
                findCount(counter - 1);
            });
        }

        return previousCount.promise;
    };

    // munge the raw event from the backend into the event_queue's format
    var mungeEvent = function(event) {
        var mungedEventDefer = $q.defer();

        // basic data needed in the munged event
        var mungedEvent = {
            counter: event.counter,
            id: event.id,
            processed: false,
            name: event.event_name
        };

        // for different types of events, you need different types of data
        if (event.event_name === 'playbook_on_start') {
            mungedEvent.count = {
                ok: 0,
                skipped: 0,
                unreachable: 0,
                failures: 0,
                changed: 0
            };
            mungedEvent.changes = ['count'];
            mungedEventDefer.resolve(mungedEvent);
        } else if (event.event_name === 'runner_on_ok' ||
            event.event_name === 'runner_on_async_ok') {
                getPreviousCount(mungedEvent.counter)
                    .then(count => {
                        mungedEvent.count = count;
                        mungedEvent.count.ok++;
                        mungedEvent.changes = ['count'];
                        mungedEventDefer.resolve(mungedEvent);
                    });
        } else if (event.event_name === 'runner_on_skipped') {
            getPreviousCount(mungedEvent.counter)
                .then(count => {
                    mungedEvent.count = count;
                    mungedEvent.count.skipped++;
                    mungedEvent.changes = ['count'];
                    mungedEventDefer.resolve(mungedEvent);
                });
        } else if (event.event_name === 'runner_on_unreachable') {
            getPreviousCount(mungedEvent.counter)
                .then(count => {
                    mungedEvent.count = count;
                    mungedEvent.count.unrecahble++;
                    mungedEvent.changes = ['count'];
                    mungedEventDefer.resolve(mungedEvent);
                });
        } else if (event.event_name === 'runner_on_error' ||
            event.event_name === 'runner_on_async_failed') {
                getPreviousCount(mungedEvent.counter)
                    .then(count => {
                        mungedEvent.count = count;
                        mungedEvent.count.failed++;
                        mungedEvent.changes = ['count'];
                        mungedEventDefer.resolve(mungedEvent);
                    });
        } else if (event.event_name === 'playbook_on_stats') {
            // get the data for populating the host status bar
            mungedEvent.count = jobResultsService
                .getCountsFromStatsEvent(event.event_data);
            mungedEvent.changes = ['count', 'countFinished'];
            mungedEventDefer.resolve(mungedEvent);
        } else {
            mungedEventDefer.resolve(mungedEvent);
        }

        return mungedEventDefer.promise;
    };

    val = {
        populateDefers: {},
        queue: {},
        // reinitializes the event queue value for the job results page
        //
        // TODO: implement some sort of local storage scheme
        // to make viewing job details that the user has
        // previous clicked on super quick, this would be where you grab
        // from local storage
        initialize: function() {
            val.queue = {};
            val.populateDefers = {};
        },
        // populates the event queue
        populate: function(event) {
            // if a defer hasn't been set up for the event,
            // set one up now
            if (!val.populateDefers[event.counter]) {
                val.populateDefers[event.counter] = $q.defer();
            }

            if (!val.queue[event.counter]) {
                var resolvePopulation = function(event) {
                    // to resolve, put the event on the queue and
                    // then resolve the deferred value
                    //
                    // TODO: implement some sort of local storage scheme
                    // to make viewing job details that the user has
                    // previous clicked on super quick, this would be
                    // where you put in local storage
                    val.queue[event.counter] = event;
                    val.populateDefers[event.counter].resolve(event);
                }

                if (event.counter === 1) {
                    // for the first event, go ahead and munge and
                    // resolve
                    mungeEvent(event).then(event => {
                        resolvePopulation(event);
                    });
                } else {
                    // for all other events, you have to do some things
                    // to keep the event processing in the UI synchronous

                    if (!val.populateDefers[event.counter - 1]) {
                        // first, if the previous event doesn't have
                        // a defer set up (this happens when websocket
                        // events are coming in and you need to make
                        // rest calls to catch up), go ahead and set a
                        // defer for the previous event
                        val.populateDefers[event.counter - 1] = $q.defer();
                    }

                    // you can start the munging process...
                    mungeEvent(event).then(event => {
                        // ...but wait until the previous event has
                        // been resolved before resolving this one and
                        // doing stuff in the ui (that's why we
                        // needed that previous conditional).  this
                        // could be done in a more asynchronous nature
                        // if we need a performance boost.  See the
                        // todo note in the markProcessed function
                        // for an idea
                        val.populateDefers[event.counter - 1].promise
                            .then(() => {
                                resolvePopulation(event);
                            });
                    });
                }
            } else {
                // don't repopulate the event if it's already been added
                // and munged either by rest or by websocket event
                val.populateDefers[event.counter]
                    .resolve(val.queue[event.counter]);
            }

            return val.populateDefers[event.counter].promise;
        },
        // the event has been processed in the view and should be marked as
        // completed in the queue
        markProcessed: function(event) {
            var process = function(event) {
                // the event has now done it's work in the UI, record
                // that!
                val.queue[event.counter].processed = true;

                // TODO: we can actually record what has been done in the
                // UI and at what event too!  (something like "resolved
                // the count on event 63)".
                //
                // if we do something like this, we actually wouldn't
                // have to wait until the previous events had completed
                // before resolving and returning to the controller
                // in populate()...
                // in other words, we could send events out of order to
                // the controller, but let the controller know that it's
                // an older event that what is in the view so we don't
                // need to do anything
            };

            if (!val.queue[event.counter]) {
                // sometimes, the process is called in the controller and
                // the event queue hasn't caught up and actually added
                // the event to the queue yet.  Wait until that happens
                val.populateDefers[event.counter].promise
                    .finally(function() {
                        process(event);
                    });
            } else {
                process(event);
            }
        }
    };

    return val;
}];
