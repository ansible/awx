export default ['jobData', 'jobDataOptions', 'jobLabels', '$scope', 'ParseTypeChange', 'ParseVariableString', 'jobResultsService', '$rootScope', 'eventQueue', function(jobData, jobDataOptions, jobLabels, $scope, ParseTypeChange, ParseVariableString, jobResultsService, $rootScope, eventQueue) {
    var getTowerLinks = function() {
        var getTowerLink = function(key) {
            if ($scope.job.related[key]) {
                return '/#/' + $scope.job.related[key]
                    .split('api/v1/')[1];
            } else {
                return null;
            }
        };

        $scope.job_template_link = getTowerLink('job_template');
        $scope.created_by_link = getTowerLink('created_by');
        $scope.inventory_link = getTowerLink('inventory');
        $scope.project_link = getTowerLink('project');
        $scope.machine_credential_link = getTowerLink('credential');
        $scope.cloud_credential_link = getTowerLink('cloud_credential');
        $scope.network_credential_link = getTowerLink('network_credential');
    };

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

        $scope.status_label = getTowerLabel('status');
        $scope.type_label = getTowerLabel('job_type');
        $scope.verbosity_label = getTowerLabel('verbosity');
    };

    // put initially resolved request data on scope
    $scope.job = jobData;
    $scope.jobOptions = jobDataOptions.actions.GET;
    $scope.labels = jobLabels;

    // turn related api browser routes into tower routes
    getTowerLinks();

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

    // EVENT STUFF BELOW

    // just putting the event queue on scope so it can be inspected in the
    // console
    $scope.event_queue = eventQueue.queue;

    var processEvent = function(event) {
        // put the event in the queue
        var mungedEvent = eventQueue.populate(event);

        // make changes to ui based on the event returned from the queue
        mungedEvent.changes.forEach(change => {
            if (change === 'count') {
                $scope.count = mungedEvent.count;
            }
        });

        // the changes have been processed in the ui, mark it in the queue
        eventQueue.markProcessed(event);
    };

    // grab completed event data and process each event
    jobResultsService.getEvents($scope.job)
        .then(events => {
            events.forEach(event => {
                // get the name in the same format as the data
                // coming over the websocket
                event.event_name = event.event;
                processEvent(event);
            });
        });

    // process incoming job events
    $rootScope.event_socket.on("job_events-" + $scope.job.id, function(data) {
        processEvent(data);
    });

    // process incoming job status changes
    $rootScope.$on('JobStatusChange-jobDetails', function(e, data) {
        if (parseInt(data.unified_job_id, 10) === parseInt($scope.job.id,10)) {
            $scope.job.status = data.status;
        }
    });
}];
