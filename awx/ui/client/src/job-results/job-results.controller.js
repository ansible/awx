export default ['jobData', 'jobDataOptions', 'jobLabels', '$scope', 'ParseTypeChange', 'ParseVariableString', 'jobResultsService', '$rootScope', 'eventQueue', function(jobData, jobDataOptions, jobLabels, $scope, ParseTypeChange, ParseVariableString, jobResultsService, $rootScope, eventQueue) {
    // just putting the event queue on scope so it can be inspected in the
    // console
    $scope.event_queue = eventQueue.queue;

    var processEvent = function(event) {
        // put the event in the queue
        eventQueue.populate(event);

        if(event.event_name === "playbook_on_stats"){
            // get the data for populating the host status bar
            $scope.count = jobResultsService
                .getHostStatusBarCounts(event.event_data);

            // mark the event as processed in the queue;
            eventQueue.markProcessed(event);
        }
    }

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

    // Initially set the count data to have no hosts as finsihed
    $scope.count = {ok: 0, skipped: 0, unreachable: 0, failures: 0, changed: 0};

    $scope.deleteJob = function() {
        jobResultsService.deleteJob($scope.job);
    };

    $scope.cancelJob = function() {
        jobResultsService.cancelJob($scope.job);
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
        })

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
