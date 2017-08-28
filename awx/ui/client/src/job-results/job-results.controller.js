export default ['jobData', 'jobDataOptions', 'jobLabels', 'jobFinished', 'count', '$scope', 'ParseTypeChange',
            'ParseVariableString', 'jobResultsService', 'eventQueue', '$compile', '$log', 'Dataset', '$q',
            'QuerySet', '$rootScope', 'moment', '$stateParams', 'i18n', 'fieldChoices', 'fieldLabels',
            'workflowResultsService', 'statusSocket', 'GetBasePath', '$state', 'jobExtraCredentials',
function(jobData, jobDataOptions, jobLabels, jobFinished, count, $scope, ParseTypeChange,
    ParseVariableString, jobResultsService, eventQueue, $compile, $log, Dataset, $q,
    QuerySet, $rootScope, moment, $stateParams, i18n, fieldChoices, fieldLabels,
    workflowResultsService, statusSocket, GetBasePath, $state, jobExtraCredentials) {

    var toDestroy = [];
    var cancelRequests = false;
    var runTimeElapsedTimer = null;

    // download stdout tooltip text
    $scope.standardOutTooltip = i18n._('Download Output');

    // stdout full screen toggle tooltip text
    $scope.toggleStdoutFullscreenTooltip = i18n._("Expand Output");

    // this allows you to manage the timing of rest-call based events as
    // filters are updated.  see processPage for more info
    var currentContext = 1;
    $scope.firstCounterFromSocket = -1;

    $scope.explanationLimit = 150;

    // if the user enters the page mid-run, reset the search to include a param
    // to only grab events less than the first counter from the websocket events
    toDestroy.push($scope.$watch('firstCounterFromSocket', function(counter) {
        if (counter > -1) {
            // make it so that the search include a counter less than the
            // first counter from the socket
            let params = _.cloneDeep($stateParams.job_event_search);
            params.counter__lte = "" + counter;

            Dataset = QuerySet.search(jobData.related.job_events,
                params);

            Dataset.then(function(actualDataset) {
                $scope.job_event_dataset = actualDataset.data;
            });
        }
    }));

    // used for tag search
    $scope.job_event_dataset = Dataset.data;

    // used for tag search
    $scope.list = {
        basePath: jobData.related.job_events,
        name: 'job_events'
    };

    // used for tag search
    $scope.job_events = $scope.job_event_dataset.results;

    $scope.jobExtraCredentials = jobExtraCredentials;

    var getLinks = function() {
        var getLink = function(key) {
            if(key === 'schedule') {
                if($scope.job.related.schedule) {
                    return '/#/templates/job_template/' + $scope.job.job_template + '/schedules' + $scope.job.related.schedule.split(/api\/v\d+\/schedules/)[1];
                }
                else {
                    return null;
                }
            }
            else if(key === 'inventory') {
                if($scope.job.summary_fields.inventory && $scope.job.summary_fields.inventory.id) {
                    if($scope.job.summary_fields.inventory.kind && $scope.job.summary_fields.inventory.kind === 'smart') {
                        return '/#/inventories/smart/' + $scope.job.summary_fields.inventory.id;
                    }
                    else {
                        return '/#/inventories/inventory/' + $scope.job.summary_fields.inventory.id;
                    }
                }
                else {
                    return null;
                }
            }
            else {
                if ($scope.job.related[key]) {
                    return '/#/' + $scope.job.related[key]
                        .split(/api\/v\d+\//)[1];
                } else {
                    return null;
                }
            }
        };

        $scope.created_by_link = getLink('created_by');
        $scope.scheduled_by_link = getLink('schedule');
        $scope.inventory_link = getLink('inventory');
        $scope.project_link = getLink('project');
        $scope.machine_credential_link = getLink('credential');
        $scope.cloud_credential_link = getLink('cloud_credential');
        $scope.network_credential_link = getLink('network_credential');
        $scope.vault_credential_link = getLink('vault_credential');
        $scope.schedule_link = getLink('schedule');
    };

    // uses options to set scope variables to their readable string
    // value
    var getLabels = function() {
        var getLabel = function(key) {
            if ($scope.jobOptions && $scope.jobOptions[key]) {
                return $scope.jobOptions[key].choices
                    .filter(val => val[0] === $scope.job[key])
                    .map(val => val[1])[0];
            } else {
                return null;
            }
        };

        $scope.type_label = getLabel('job_type');
        $scope.verbosity_label = getLabel('verbosity');
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

    $scope.previousTaskFailed = false;

    toDestroy.push($scope.$watch('job.job_explanation', function(explanation) {
        if (explanation && explanation.split(":")[0] === "Previous Task Failed") {
            $scope.previousTaskFailed = true;

            var taskObj = JSON.parse(explanation.substring(explanation.split(":")[0].length + 1));
            // return a promise from the options request with the permission type choices (including adhoc) as a param
            var fieldChoice = fieldChoices({
                $scope: $scope,
                url: GetBasePath('unified_jobs'),
                field: 'type'
            });

            // manipulate the choices from the options request to be set on
            // scope and be usable by the list form
            fieldChoice.then(function (choices) {
                choices =
                    fieldLabels({
                        choices: choices
                    });
                $scope.explanation_fail_type = choices[taskObj.job_type];
                $scope.explanation_fail_name = taskObj.job_name;
                $scope.explanation_fail_id = taskObj.job_id;
                $scope.task_detail = $scope.explanation_fail_type + " failed for " + $scope.explanation_fail_name + " with ID " + $scope.explanation_fail_id + ".";
            });
        } else {
            $scope.previousTaskFailed = false;
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

    // turn related api browser routes into front end routes
    getLinks();

    // the links below can't be set in getLinks because the
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
    getLabels();

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

        if ($scope.stdoutFullScreen === true) {
            $scope.toggleStdoutFullscreenTooltip = i18n._("Collapse Output");
        } else if ($scope.stdoutFullScreen === false) {
            $scope.toggleStdoutFullscreenTooltip = i18n._("Expand Output");
        }
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
        $scope.followTooltip = i18n._("Jump to last line of standard out.");
    } else {
        $scope.followTooltip = i18n._("Currently following standard out as it comes in.  Click to unfollow.");
    }

    $scope.events = {};

    function updateJobElapsedTimer(time) {
        $scope.job.elapsed = time;
    }

    // For elapsed time while a job is running, compute the differnce in seconds,
    // from the time the job started until now. Moment() returns the current
    // time as a moment object.
    if ($scope.job.started !== null && $scope.job.status === 'running') {
        runTimeElapsedTimer = workflowResultsService.createOneSecondTimer($scope.job.started, updateJobElapsedTimer);
    }

    // EVENT STUFF BELOW
    var linesInPane = [];

    function addToLinesInPane(event) {
        var arr = _.range(event.start_line, event.actual_end_line);
        linesInPane = linesInPane.concat(arr);
        linesInPane = linesInPane.sort(function(a, b) {
            return a - b;
        });
    }

    function appendToBottom (event){
        // if we get here then the event type was either a
        // header line, recap line, or one of the additional
        // event types, so we append it to the bottom.
        // These are the event types for captured
        // stdout not directly related to playbook or runner
        // events:
        // (0, 'debug', _('Debug'), False),
        // (0, 'verbose', _('Verbose'), False),
        // (0, 'deprecated', _('Deprecated'), False),
        // (0, 'warning', _('Warning'), False),
        // (0, 'system_warning', _('System Warning'), False),
        // (0, 'error', _('Error'), True),
        angular
            .element(".JobResultsStdOut-stdoutContainer")
            .append($compile(event
                .stdout)($scope.events[event
                    .counter]));
    }

    function putInCorrectPlace(event) {
        if (linesInPane.length) {
            for (var i = linesInPane.length - 1; i >= 0; i--) {
                if (event.start_line > linesInPane[i]) {
                    $(`.line_num_${linesInPane[i]}`)
                        .after($compile(event
                            .stdout)($scope.events[event
                                .counter]));
                    i = -1;
                }
            }
        } else {
            appendToBottom(event);
        }
    }

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
                    $scope.followTooltip = i18n._("Jump to last line of standard out.");
                    if ($scope.followEngaged) {
                        if (!$scope.followScroll) {
                            $scope.followScroll = function() {
                                $log.error("follow scroll undefined, standard out directive not loaded yet?");
                            };
                        }
                        $scope.followScroll();
                    }
                }

                if (change === 'countFinished') {
                    // the playbook_on_stats event actually lets
                    // us know that we don't need to iteratively
                    // look at event to update the host counts
                    // any more.
                    $scope.countFinished = true;
                }

                if(change === 'stdout'){
                    if (!$scope.events[mungedEvent.counter]) {
                        // line hasn't been put in the pane yet

                        // create new child scope
                        $scope.events[mungedEvent.counter] = $scope.$new();
                        $scope.events[mungedEvent.counter]
                            .event = mungedEvent;

                        // let's see if we have a specific place to put it in
                        // the pane
                        let $prevElem = $(`.next_is_${mungedEvent.start_line}`);
                        if ($prevElem && $prevElem.length) {
                            // if so, put it there
                            $(`.next_is_${mungedEvent.start_line}`)
                                .after($compile(mungedEvent
                                    .stdout)($scope.events[mungedEvent
                                        .counter]));
                            addToLinesInPane(mungedEvent);
                        } else {
                            var putIn;
                            var classList = $("div",
                                "<div>"+mungedEvent.stdout+"</div>")
                                .attr("class").split(" ");
                            if (classList
                                .filter(v => v.indexOf("task_") > -1)
                                .length) {
                                putIn = classList
                                    .filter(v => v.indexOf("task_") > -1)[0];
                            } else if(classList
                                .filter(v => v.indexOf("play_") > -1)
                                .length) {
                                putIn = classList
                                    .filter(v => v.indexOf("play_") > -1)[0];
                            }

                            var putAfter;
                            var isDup = false;

                            if ($(".header_" + putIn + ",." + putIn).length === 0) {
                                putInCorrectPlace(mungedEvent);
                                addToLinesInPane(mungedEvent);
                            } else {
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
                                        }  else {
                                            appendToBottom(mungedEvent);
                                            addToLinesInPane(mungedEvent);
                                        }
                                    });
                            }

                            if (!isDup && putAfter) {
                                addToLinesInPane(mungedEvent);
                                $(putAfter).after($compile(mungedEvent
                                    .stdout)($scope.events[mungedEvent
                                        .counter]));
                            }


                            classList = null;
                            putIn = null;
                        }

                        // delete ref to the elem because it might leak scope
                        // if you don't
                        $prevElem = null;
                    }

                    // move the followAnchor to the bottom of the
                    // container
                    $(".JobResultsStdOut-followAnchor")
                        .appendTo(".JobResultsStdOut-stdoutContainer");
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


    // used to show a message to just download for old jobs
    // remove in 3.2.0
    $scope.isOld = 0;
    $scope.showLegacyJobErrorMessage = false;

    toDestroy.push($scope.$watch('isOld', function (val) {
        if (val >= 2) {
            $scope.showLegacyJobErrorMessage = true;
        }
    }));

    // get header and recap lines
    var skeletonPlayCount = 0;
    var skeletonTaskCount = 0;
    var getSkeleton = function(url) {
        jobResultsService.getEvents(url)
            .then(events => {
                events.results.forEach(event => {
                    if (event.start_line === 0 && event.end_line === 0) {
                        $scope.isOld++;
                    }
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
        getSkeleton(jobData.related.job_events + "?order_by=start_line&or__event__in=playbook_on_start,playbook_on_play_start,playbook_on_task_start,playbook_on_stats");
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
        //
        // also, if the page doesn't contain results (i.e.: the response
        // returns an error), don't process the page
        if (context !== currentContext || events === undefined ||
            events.results === undefined) {
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
        if (val) {
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
                if (val.count > parseInt(val.maxEvents)) {
                    $(".header_task").hide();
                    $(".header_play").hide();
                    $scope.standardOutTooltip = '<div class="JobResults-downloadTooLarge"><div>' +
                        i18n._('The output is too large to display. Please download.') +
                        '</div>' +
                        '<div class="JobResults-downloadTooLarge--icon">' +
                        '<span class="fa-stack fa-lg">' +
                        '<i class="fa fa-circle fa-stack-1x"></i>' +
                        '<i class="fa fa-stack-1x icon-job-stdout-download-tooltip"></i>' +
                        '</span>' +
                        '</div>' +
                        '</div>';

                    if ($scope.job_status === "successful" ||
                        $scope.job_status === "failed" ||
                        $scope.job_status === "error" ||
                        $scope.job_status === "canceled") {
                        $scope.tooManyEvents = true;
                        $scope.tooManyPastEvents = false;
                    } else {
                        $scope.tooManyPastEvents = true;
                        $scope.tooManyEvents = false;
                        $scope.gotPreviouslyRanEvents.resolve("");
                    }
                } else {
                    $(".header_task").show();
                    $(".header_play").show();
                    $scope.tooManyEvents = false;
                    $scope.tooManyPastEvents = false;
                    processPage(val, context);
                }
            });
        }
    }));

    var buffer = [];

    var processBuffer = function() {
        var follow = function() {
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
        };

        for (let i = 0; i < 4; i++) {
            processEvent(buffer[i]);
            buffer.splice(i, 1);
        }

        follow();
    };

    var bufferInterval;

    // Processing of job_events messages from the websocket
    toDestroy.push($scope.$on(`ws-job_events-${$scope.job.id}`, function(e, data) {
        if (!bufferInterval) {
            bufferInterval = setInterval(function(){
                processBuffer();
            }, 500);
        }

        // use the lowest counter coming over the socket to retrigger pull data
        // to only be for stuff lower than that id
        //
        // only do this for entering the jobs page mid-run (thus the
        // data.counter is 1 conditional
        if (data.counter === 1) {
          $scope.firstCounterFromSocket = -2;
        }

        if ($scope.firstCounterFromSocket !== -2 &&
            $scope.firstCounterFromSocket === -1 ||
            data.counter < $scope.firstCounterFromSocket) {
                $scope.firstCounterFromSocket = data.counter;
        }

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
            buffer.push(data);
        });
    }));

    // get previously set up socket messages from resolve
    if (statusSocket && statusSocket[0] && statusSocket[0].job_status) {
        $scope.job_status = statusSocket[0].job_status;
    }
    if ($scope.job_status === "running" && !$scope.job.elapsed) {
        runTimeElapsedTimer = workflowResultsService.createOneSecondTimer(moment(), updateJobElapsedTimer);
    }

    // Processing of job-status messages from the websocket
    toDestroy.push($scope.$on(`ws-jobs`, function(e, data) {
        if (parseInt(data.unified_job_id, 10) ===
            parseInt($scope.job.id,10)) {
            // controller is defined, so set the job_status
            $scope.job_status = data.status;
            if(_.has(data, 'instance_group_name')){
                $scope.job.instance_group = true;
                $scope.job.summary_fields.instance_group = {
                    "name": data.instance_group_name
                };
            }
            if (data.status === "running") {
                if (!runTimeElapsedTimer) {
                    runTimeElapsedTimer = workflowResultsService.createOneSecondTimer(moment(), updateJobElapsedTimer);
                }
            } else if (data.status === "successful" ||
                data.status === "failed" ||
                data.status === "error" ||
                data.status === "canceled") {
                    workflowResultsService.destroyTimer(runTimeElapsedTimer);

                    // When the fob is finished retrieve the job data to
                    // correct anything that was out of sync from the job run
                    jobResultsService.getJobData($scope.job.id).then(function(data){
                        $scope.job = data;
                        $scope.jobFinished = true;
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

    if (statusSocket && statusSocket[1]) {
        statusSocket[1]();
    }

    $scope.$on('$destroy', function(){
        if (statusSocket && statusSocket[1]) {
            statusSocket[1]();
        }
        $( ".JobResultsStdOut-aLineOfStdOut" ).remove();
        cancelRequests = true;
        eventQueue.initialize();
        Object.keys($scope.events)
            .forEach(v => {
                $scope.events[v].$destroy();
                $scope.events[v] = null;
            });
        $scope.events = {};
        workflowResultsService.destroyTimer(runTimeElapsedTimer);
        if (bufferInterval) {
            clearInterval(bufferInterval);
        }
        toDestroy.forEach(closureFunc => closureFunc());
    });
}];
