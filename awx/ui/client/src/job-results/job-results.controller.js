export default ['jobData', 'jobDataOptions', 'jobLabels', 'jobFinished', 'count', '$scope', 'ParseTypeChange', 'ParseVariableString', 'jobResultsService', 'eventQueue', '$compile', '$log', 'Dataset', '$q', 'Rest', '$state', 'QuerySet', '$rootScope', 'moment',
function(jobData, jobDataOptions, jobLabels, jobFinished, count, $scope, ParseTypeChange, ParseVariableString, jobResultsService, eventQueue, $compile, $log, Dataset, $q, Rest, $state, QuerySet, $rootScope, moment) {
    var toDestroy = [];
    var cancelRequests = false;

    // this allows you to manage the timing of rest-call based events as
    // filters are updated.  see processPage for more info
    var currentContext = 1;

    // used for tag search
    $scope.job_event_dataset = Dataset.data;

    // used for tag search
    $scope.list = {
        basePath: jobData.related.job_events,
        defaultSearchParams: function(term){
            return {
                or__stdout__icontains: term,
            };
        },
    };

    // used for tag search
    $scope.job_events = $scope.job_event_dataset.results;

    var getTowerLinks = function() {
        var getTowerLink = function(key) {
            if ($scope.job.related[key]) {
                return '/#/' + $scope.job.related[key]
                    .split('api/v1/')[1];
            } else {
                return null;
            }
        };

        $scope.created_by_link = getTowerLink('created_by');
        $scope.inventory_link = getTowerLink('inventory');
        $scope.project_link = getTowerLink('project');
        $scope.machine_credential_link = getTowerLink('credential');
        $scope.cloud_credential_link = getTowerLink('cloud_credential');
        $scope.network_credential_link = getTowerLink('network_credential');
        $scope.schedule_link = getTowerLink('schedule');
    };

    // uses options to set scope variables to their readable string
    // value
    var getTowerLabels = function() {
        var getTowerLabel = function(key) {
            if ($scope.jobOptions && $scope.jobOptions[key]) {
                return $scope.jobOptions[key].choices
                    .filter(val => val[0] === $scope.job[key])
                    .map(val => val[1])[0];
            } else {
                return null;
            }
        };

        $scope.type_label = getTowerLabel('job_type');
        $scope.verbosity_label = getTowerLabel('verbosity');
    };

    var getTotalHostCount = function(count) {
        return Object
            .keys(count).reduce((acc, i) => acc += count[i], 0);
    };

    // put initially resolved request data on scope
    $scope.job = jobData;
    $scope.jobOptions = jobDataOptions.actions.GET;
    $scope.labels = jobLabels;
    $scope.jobFinished = jobFinished;

    // update label in left pane and tooltip in right pane when the job_status
    // changes
    toDestroy.push($scope.$watch('job_status', function(status) {
        if (status) {
            $scope.status_label = $scope.jobOptions.status.choices
                .filter(val => val[0] === status)
                .map(val => val[1])[0];
            $scope.status_tooltip = "Job " + $scope.status_label;
        }
    }));

    // update the job_status value.  Use the cached rootScope value if there
    // is one.  This is a workaround when the rest call for the jobData is
    // made before some socket events come in for the job status
    if ($rootScope['lastSocketStatus' + jobData.id]) {
        $scope.job_status = $rootScope['lastSocketStatus' + jobData.id];
        delete $rootScope['lastSocketStatus' + jobData.id];
    } else {
        $scope.job_status = jobData.status;
    }

    // turn related api browser routes into tower routes
    getTowerLinks();

    // the links below can't be set in getTowerLinks because the
    // links on the UI don't directly match the corresponding URL
    // on the API browser
    if(jobData.summary_fields && jobData.summary_fields.job_template &&
        jobData.summary_fields.job_template.id){
            $scope.job_template_link = `/#/templates/job_template/${$scope.job.summary_fields.job_template.id}`;
    }
    if(jobData.summary_fields && jobData.summary_fields.project_update &&
        jobData.summary_fields.project_update.status){
            $scope.project_status = jobData.summary_fields.project_update.status;
    }
    if(jobData.summary_fields && jobData.summary_fields.project_update &&
        jobData.summary_fields.project_update.id){
            $scope.project_update_link = `/#/scm_update/${jobData.summary_fields.project_update.id}`;
    }
    if(jobData.summary_fields && jobData.summary_fields.source_workflow_job &&
        jobData.summary_fields.source_workflow_job.id){
            $scope.workflow_result_link = `/#/workflows/${jobData.summary_fields.source_workflow_job.id}`;
    }
    if(jobData.result_traceback) {
        $scope.job.result_traceback = jobData.result_traceback.trim().split('\n').join('<br />');
    }
    // use options labels to manipulate display of details
    getTowerLabels();

    // set up a read only code mirror for extra vars
    $scope.variables = ParseVariableString($scope.job.extra_vars);
    $scope.parseType = 'yaml';
    ParseTypeChange({ scope: $scope,
        field_id: 'pre-formatted-variables',
        readOnly: true });

    // Click binding for the expand/collapse button on the standard out log
    $scope.stdoutFullScreen = false;
    $scope.toggleStdoutFullscreen = function() {
        $scope.stdoutFullScreen = !$scope.stdoutFullScreen;
    };

    $scope.deleteJob = function() {
        jobResultsService.deleteJob($scope.job);
    };

    $scope.cancelJob = function() {
        jobResultsService.cancelJob($scope.job);
    };

    $scope.relaunchJob = function() {
        jobResultsService.relaunchJob($scope);
    };

    $scope.lessLabels = false;
    $scope.toggleLessLabels = function() {
        if (!$scope.lessLabels) {
            $('#job-results-labels').slideUp(200);
            $scope.lessLabels = true;
        }
        else {
            $('#job-results-labels').slideDown(200);
            $scope.lessLabels = false;
        }
    };

    // get initial count from resolve
    $scope.count = count.val;
    $scope.hostCount = getTotalHostCount(count.val);
    $scope.countFinished = count.countFinished;

    // if the job is still running engage following of the last line in the
    // standard out pane
    $scope.followEngaged = !$scope.jobFinished;

    // follow button for completed job should specify that the
    // button will jump to the bottom of the standard out pane,
    // not follow lines as they come in
    if ($scope.jobFinished) {
        $scope.followTooltip = "Jump to last line of standard out.";
    } else {
        $scope.followTooltip = "Currently following standard out as it comes in.  Click to unfollow.";
    }

    $scope.events = {};

    // For elapsed time while a job is running, compute the differnce in seconds,
    // from the time the job started until now. Moment() returns the current
    // time as a moment object.
    var start = ($scope.job.started === null) ? moment() : moment($scope.job.started);
    if(jobFinished === false){
        var elapsedInterval = setInterval(function(){
            let now = moment();
            $scope.job.elapsed = now.diff(start, 'seconds');
        }, 1000);
    }

    // EVENT STUFF BELOW

    // This is where the async updates to the UI actually happen.
    // Flow is event queue munging in the service -> $scope setting in here
    var processEvent = function(event, context) {
        // only care about filter context checking when the event comes
        // as a rest call
        if (context && context !== currentContext) {
            return;
        }
        // put the event in the queue
        var mungedEvent = eventQueue.populate(event);

        // make changes to ui based on the event returned from the queue
        if (mungedEvent.changes) {
            mungedEvent.changes.forEach(change => {
                // we've got a change we need to make to the UI!
                // update the necessary scope and make the change
                if (change === 'startTime' && !$scope.job.start) {
                    $scope.job.start = mungedEvent.startTime;
                }

                if (change === 'count' && !$scope.countFinished) {
                    // for all events that affect the host count,
                    // update the status bar as well as the host
                    // count badge
                    $scope.count = mungedEvent.count;
                    $scope.hostCount = getTotalHostCount(mungedEvent
                        .count);
                }

                if (change === 'finishedTime'  && !$scope.job.finished) {
                    $scope.job.finished = mungedEvent.finishedTime;
                    $scope.jobFinished = true;
                    $scope.followTooltip = "Jump to last line of standard out.";
                }

                if (change === 'countFinished') {
                    // the playbook_on_stats event actually lets
                    // us know that we don't need to iteratively
                    // look at event to update the host counts
                    // any more.
                    $scope.countFinished = true;
                }

                if(change === 'stdout'){
                    // put stdout elements in stdout container

                    // this scopes the event to that particular
                    // block of stdout.
                    // If you need to see the event a particular
                    // stdout block is from, you can:
                    // angular.element($0).scope().event
                    $scope.events[mungedEvent.counter] = $scope.$new();
                    $scope.events[mungedEvent.counter]
                        .event = mungedEvent;

                    if (mungedEvent.stdout.indexOf("not_skeleton") > -1) {
                        // put non-duplicate lines into the standard
                        // out pane where they should go (within the
                        // right header section, before the next line
                        // as indicated by start_line)
                        window.$ = $;
                        var putIn;
                        var classList = $("div",
                            "<div>"+mungedEvent.stdout+"</div>")
                            .attr("class").split(" ");
                        if (classList
                            .filter(v => v.indexOf("task_") > -1)
                            .length) {
                            putIn = classList
                                .filter(v => v.indexOf("task_") > -1)[0];
                        } else {
                            putIn = classList
                                .filter(v => v.indexOf("play_") > -1)[0];
                        }

                        var putAfter;
                        var isDup = false;
                        $(".header_" + putIn + ",." + putIn)
                            .each((i, v) => {
                                if (angular.element(v).scope()
                                    .event.start_line < mungedEvent
                                    .start_line) {
                                    putAfter = v;
                                } else if (angular.element(v).scope()
                                    .event.start_line === mungedEvent
                                    .start_line) {
                                    isDup = true;
                                    return false;
                                } else if (angular.element(v).scope()
                                    .event.start_line > mungedEvent
                                    .start_line) {
                                    return false;
                                }
                            });

                        if (!isDup) {
                            $(putAfter).after($compile(mungedEvent
                                .stdout)($scope.events[mungedEvent
                                    .counter]));
                        }

                        classList = null;
                        putIn = null;
                    } else {
                        // this is a header or recap line, so just
                        // append to the bottom
                        angular
                            .element(".JobResultsStdOut-stdoutContainer")
                            .append($compile(mungedEvent
                                .stdout)($scope.events[mungedEvent
                                    .counter]));
                    }

                    // move the followAnchor to the bottom of the
                    // container
                    $(".JobResultsStdOut-followAnchor")
                        .appendTo(".JobResultsStdOut-stdoutContainer");

                    // if follow is engaged,
                    // scroll down to the followAnchor
                    if ($scope.followEngaged) {
                        if (!$scope.followScroll) {
                            $scope.followScroll = function() {
                                $log.error("follow scroll undefined, standard out directive not loaded yet?");
                            };
                        }
                        $scope.followScroll();
                    }
                }
            });

            // the changes have been processed in the ui, mark it in the
            // queue
            eventQueue.markProcessed(event);
        }
    };

    $scope.stdoutContainerAvailable = $q.defer();
    $scope.hasSkeleton = $q.defer();

    eventQueue.initialize();

    $scope.playCount = 0;
    $scope.taskCount = 0;

    // get header and recap lines
    var skeletonPlayCount = 0;
    var skeletonTaskCount = 0;
    var getSkeleton = function(url) {
        jobResultsService.getEvents(url)
            .then(events => {
                events.results.forEach(event => {
                    // get the name in the same format as the data
                    // coming over the websocket
                    event.event_name = event.event;
                    delete event.event;

                    // increment play and task count
                    if (event.event_name === "playbook_on_play_start") {
                        skeletonPlayCount++;
                    } else if (event.event_name === "playbook_on_task_start") {
                        skeletonTaskCount++;
                    }

                    processEvent(event);
                });
                if (events.next) {
                    getSkeleton(events.next);
                } else {
                    // after the skeleton requests have completed,
                    // put the play and task count into the dom
                    $scope.playCount = skeletonPlayCount;
                    $scope.taskCount = skeletonTaskCount;
                    $scope.hasSkeleton.resolve("skeleton resolved");
                }
            });
    };

    $scope.stdoutContainerAvailable.promise.then(() => {
        getSkeleton(jobData.related.job_events + "?order_by=id&or__event__in=playbook_on_start,playbook_on_play_start,playbook_on_task_start,playbook_on_stats");
    });

    var getEvents;

    var processPage = function(events, context) {
        // currentContext is the context of the filter when this request
        // to processPage was made
        //
        // currentContext is the context of the filter currently
        //
        // if they are not the same, make sure to stop process events/
        // making rest calls for next pages/etc. (you can see context is
        // also passed into getEvents and processEvent and similar checks
        // exist in these functions)
        if (context !== currentContext) {
            return;
        }

        events.results.forEach(event => {
            // get the name in the same format as the data
            // coming over the websocket
            event.event_name = event.event;
            delete event.event;

            processEvent(event, context);
        });
        if (events.next && !cancelRequests) {
            getEvents(events.next, context);
        } else {
            // put those paused events into the pane
            $scope.gotPreviouslyRanEvents.resolve("");
        }
    };

    // grab non-header recap lines
    getEvents = function(url, context) {
        if (context !== currentContext) {
            return;
        }

        jobResultsService.getEvents(url)
            .then(events => {
                processPage(events, context);
            });
    };

    // grab non-header recap lines
    toDestroy.push($scope.$watch('job_event_dataset', function(val) {
        eventQueue.initialize();

        Object.keys($scope.events)
            .forEach(v => {
                // dont destroy scope events for skeleton lines
                let name = $scope.events[v].event.name;

                if (!(name === "playbook_on_play_start" ||
                    name === "playbook_on_task_start" ||
                    name === "playbook_on_stats")) {
                    $scope.events[v].$destroy();
                    $scope.events[v] = null;
                    delete $scope.events[v];
                }
            });

        // pause websocket events from coming in to the pane
        $scope.gotPreviouslyRanEvents = $q.defer();
        currentContext += 1;

        let context = currentContext;

        $( ".JobResultsStdOut-aLineOfStdOut.not_skeleton" ).remove();
        $scope.hasSkeleton.promise.then(() => {
            processPage(val, context);
        });
    }));



    // Processing of job_events messages from the websocket
    toDestroy.push($scope.$on(`ws-job_events-${$scope.job.id}`, function(e, data) {
        $q.all([$scope.gotPreviouslyRanEvents.promise,
            $scope.hasSkeleton.promise]).then(() => {
            // put the line in the
            // standard out pane (and increment play and task
            // count if applicable)
            if (data.event_name === "playbook_on_play_start") {
                $scope.playCount++;
            } else if (data.event_name === "playbook_on_task_start") {
                $scope.taskCount++;
            }
            processEvent(data);
        });
    }));

    // Processing of job-status messages from the websocket
    toDestroy.push($scope.$on(`ws-jobs`, function(e, data) {
        if (parseInt(data.unified_job_id, 10) ===
            parseInt($scope.job.id,10)) {
            // controller is defined, so set the job_status
            $scope.job_status = data.status;
            if (data.status === "successful" ||
                data.status === "failed" ||
                data.status === "error" ||
                data.status === "canceled") {
                    clearInterval(elapsedInterval);
                    // When the fob is finished retrieve the job data to
                    // correct anything that was out of sync from the job run
                    jobResultsService.getJobData($scope.job.id).then(function(data){
                        $scope.job = data;
                    });
            }
        } else if (parseInt(data.project_id, 10) ===
            parseInt($scope.job.project,10)) {
            // this is a project status update message, so set the
            // project status in the left pane
            $scope.project_status = data.status;
            $scope.project_update_link = `/#/scm_update/${data
                .unified_job_id}`;
        } else {
            // controller was previously defined, but is not yet defined
            // for this job.  cache the socket status on root scope
            $rootScope['lastSocketStatus' + data.unified_job_id] = data.status;
        }
    }));

    $scope.$on('$destroy', function(){
        cancelRequests = true;
        eventQueue.initialize();
        Object.keys($scope.events)
            .forEach(v => {
                $scope.events[v].$destroy();
                $scope.events[v] = null;
            });
        $scope.events = {};
        clearInterval(elapsedInterval);
        toDestroy.forEach(v => v());
    });
}];
