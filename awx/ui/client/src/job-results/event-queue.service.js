/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/


export default [function(){
    var val = {
        queue: {},
        // munge the raw event from the backend into the event_queue's format
        mungeEvent: function(event) {
            event.processed = false;
            return event;
        },
        // reinitializes the event queue value for the job results page
        initialize: function() {
            val.queue = {};
        },
        // populates the event queue
        populate: function(event) {
            var mungedEvent = val.mungeEvent(event);
            val.queue[event.id] = mungedEvent;
        },
        // the event has been processed in the view and should be marked as
        // completed in the queue
        markProcessed: function(event) {
            val.queue[event.id].processed = true;
        }
    };
    return val;
}];
