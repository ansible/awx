export default ['workflowData',
    'workflowResultsService',
    'workflowDataOptions',
    'jobLabels',
    'workflowNodes',
    '$scope',
    'ParseTypeChange',
    'ParseVariableString',
    function(workflowData,
        workflowResultsService,
        workflowDataOptions,
        jobLabels,
        workflowNodes,
        $scope,
        ParseTypeChange,
        ParseVariableString
    ) {
    var getTowerLinks = function() {
        var getTowerLink = function(key) {
            if ($scope.workflow.related[key]) {
                return '/#/' + $scope.workflow.related[key]
                    .split('api/v1/')[1];
            }
            else {
                return null;
            }
        };

        $scope.workflow_template_link = '/#/templates/workflow_job_template/'+$scope.workflow.workflow_job_template;
        $scope.created_by_link = getTowerLink('created_by');
        $scope.cloud_credential_link = getTowerLink('cloud_credential');
        $scope.network_credential_link = getTowerLink('network_credential');
    };

    var getTowerLabels = function() {
        var getTowerLabel = function(key) {
            if ($scope.workflowOptions && $scope.workflowOptions[key]) {
                return $scope.workflowOptions[key].choices
                    .filter(val => val[0] === $scope.workflow[key])
                    .map(val => val[1])[0];
            } else {
                return null;
            }
        };

        $scope.status_label = getTowerLabel('status');
        $scope.type_label = getTowerLabel('job_type');
        $scope.verbosity_label = getTowerLabel('verbosity');
    };

    // var getTotalHostCount = function(count) {
    //     return Object
    //         .keys(count).reduce((acc, i) => acc += count[i], 0);
    // };

    // put initially resolved request data on scope
    $scope.workflow = workflowData;
    $scope.workflow_nodes = workflowNodes;
    $scope.workflowOptions = workflowDataOptions.actions.GET;
    $scope.labels = jobLabels;

    // turn related api browser routes into tower routes
    getTowerLinks();

    // use options labels to manipulate display of details
    getTowerLabels();

    // set up a read only code mirror for extra vars
    $scope.variables = ParseVariableString($scope.workflow.extra_vars);
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
        workflowResultsService.deleteJob($scope.workflow);
    };

    $scope.cancelJob = function() {
        workflowResultsService.cancelJob($scope.workflow);
    };

    $scope.relaunchJob = function() {
        workflowResultsService.relaunchJob($scope);
    };

    $scope.stdoutArr = [];

    $scope.treeData = {
        data: {
            id: 1,
            canDelete: false,
            canEdit: false,
            canAddTo: true,
            isStartNode: true,
            unifiedJobTemplate: {
                name: "Workflow Launch"
            },
            children: [],
            deletedNodes: [],
            totalNodes: 0
        },
        nextIndex: 2
    };

    function buildBranch(params) {
        // params.nodeId
        // params.parentId
        // params.edgeType
        // params.nodesObj
        // params.isRoot

        let treeNode = {
            children: [],
            c: "#D7D7D7",
            id: $scope.treeData.nextIndex,
            nodeId: params.nodeId,
            canDelete: true,
            canEdit: true,
            canAddTo: true,
            placeholder: false,
            edgeType: params.edgeType,
            unifiedJobTemplate: _.clone(params.nodesObj[params.nodeId].summary_fields.unified_job_template),
            isNew: false,
            edited: false,
            originalEdge: params.edgeType,
            originalNodeObj: _.clone(params.nodesObj[params.nodeId]),
            promptValues: {},
            isRoot: params.isRoot ? params.isRoot : false
        };

        $scope.treeData.data.totalNodes++;

        $scope.treeData.nextIndex++;

        if(params.parentId) {
            treeNode.originalParentId = params.parentId;
        }

        // Loop across the success nodes and add them recursively
        _.forEach(params.nodesObj[params.nodeId].success_nodes, function(successNodeId) {
            treeNode.children.push(buildBranch({
                nodeId: successNodeId,
                parentId: params.nodeId,
                edgeType: "success",
                nodesObj: params.nodesObj
            }));
        });

        // failure nodes
        _.forEach(params.nodesObj[params.nodeId].failure_nodes, function(failureNodesId) {
            treeNode.children.push(buildBranch({
                nodeId: failureNodesId,
                parentId: params.nodeId,
                edgeType: "failure",
                nodesObj: params.nodesObj
            }));
        });

        // always nodes
        _.forEach(params.nodesObj[params.nodeId].always_nodes, function(alwaysNodesId) {
            treeNode.children.push(buildBranch({
                nodeId: alwaysNodesId,
                parentId: params.nodeId,
                edgeType: "always",
                nodesObj: params.nodesObj
            }));
        });

        return treeNode;
    }


    let nodesArray = $scope.workflow_nodes;
    let nodesObj = {};
    let nonRootNodeIds = [];
    let allNodeIds = [];

    // Determine which nodes are root nodes
    _.forEach(nodesArray, function(node) {
        nodesObj[node.id] = _.clone(node);

        allNodeIds.push(node.id);

        _.forEach(node.success_nodes, function(nodeId){
        nonRootNodeIds.push(nodeId);
        });
        _.forEach(node.failure_nodes, function(nodeId){
        nonRootNodeIds.push(nodeId);
        });
        _.forEach(node.always_nodes, function(nodeId){
        nonRootNodeIds.push(nodeId);
        });
    });

    let rootNodes = _.difference(allNodeIds, nonRootNodeIds);

    // Loop across the root nodes and re-build the tree
    _.forEach(rootNodes, function(rootNodeId) {
        let branch = buildBranch({
            nodeId: rootNodeId,
            edgeType: "always",
            nodesObj: nodesObj,
            isRoot: true
        });

        $scope.treeData.data.children.push(branch);
    });

    // TODO: I think that the workflow chart directive (and eventually d3) is meddling with
    // this treeData object and removing the children object for some reason (?)
    // This happens on occasion and I think is a race condition (?)
    if(!$scope.treeData.data.children) {
        $scope.treeData.data.children = [];
    }

    $scope.canAddWorkflowJobTemplate = false;

    // EVENT STUFF BELOW

    // just putting the event queue on scope so it can be inspected in the
    // console
    // $scope.event_queue = eventQueue.queue;
    // $scope.defersArr = eventQueue.populateDefers;

    // This is where the async updates to the UI actually happen.
    // Flow is event queue munging in the service -> $scope setting in here
    // var processEvent = function(event) {
    //     // put the event in the queue
    //     eventQueue.populate(event).then(mungedEvent => {
    //         // make changes to ui based on the event returned from the queue
    //         if (mungedEvent.changes) {
    //             mungedEvent.changes.forEach(change => {
    //                 // we've got a change we need to make to the UI!
    //                 // update the necessary scope and make the change
    //                 if (change === 'startTime' && !$scope.workflow.start) {
    //                     $scope.workflow.start = mungedEvent.startTime;
    //                 }
    //
    //                 if (change === 'count' && !$scope.countFinished) {
    //                     // for all events that affect the host count,
    //                     // update the status bar as well as the host
    //                     // count badge
    //                     $scope.count = mungedEvent.count;
    //                     $scope.hostCount = getTotalHostCount(mungedEvent
    //                         .count);
    //                 }
    //
    //                 if (change === 'playCount') {
    //                     $scope.playCount = mungedEvent.playCount;
    //                 }
    //
    //                 if (change === 'taskCount') {
    //                     $scope.taskCount = mungedEvent.taskCount;
    //                 }
    //
    //                 if (change === 'finishedTime'  && !$scope.workflow.finished) {
    //                     $scope.workflow.finished = mungedEvent.finishedTime;
    //                 }
    //
    //                 if (change === 'countFinished') {
    //                     // the playbook_on_stats event actually lets
    //                     // us know that we don't need to iteratively
    //                     // look at event to update the host counts
    //                     // any more.
    //                     $scope.countFinished = true;
    //                 }
    //
    //                 if(change === 'stdout'){
    //                     angular
    //                         .element(".JobResultsStdOut-stdoutContainer")
    //                         .append($compile(mungedEvent
    //                             .stdout)($scope));
    //                 }
    //             });
    //         }
    //
    //         // the changes have been processed in the ui, mark it in the queue
    //         eventQueue.markProcessed(event);
    //     });
    // };

    // PULL! grab completed event data and process each event
    // TODO: implement retry logic in case one of these requests fails
    // var getEvents = function(url) {
    //     workflowResultsService.getEvents(url)
    //         .then(events => {
    //             events.results.forEach(event => {
    //                 // get the name in the same format as the data
    //                 // coming over the websocket
    //                 event.event_name = event.event;
    //                 processEvent(event);
    //             });
    //             if (events.next) {
    //                 getEvents(events.next);
    //             }
    //         });
    // };
    // getEvents($scope.job.related.job_events);

    // // Processing of job_events messages from the websocket
    // $scope.$on(`ws-job_events-${$scope.workflow.id}`, function(e, data) {
    //     processEvent(data);
    // });

    // Processing of job-status messages from the websocket
    $scope.$on(`ws-jobs`, function(e, data) {
        if (parseInt(data.unified_job_id, 10) === parseInt($scope.workflow.id,10)) {
            $scope.workflow.status = data.status;
        }
    });
}];
