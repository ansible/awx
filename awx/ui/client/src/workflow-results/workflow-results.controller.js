export default ['workflowData', 'workflowResultsService', 'workflowDataOptions',
    'jobLabels', 'workflowNodes', '$scope', 'ParseTypeChange',
    'ParseVariableString', 'count', '$state', 'i18n',
    'moment', function(workflowData, workflowResultsService,
    workflowDataOptions, jobLabels, workflowNodes, $scope, ParseTypeChange,
    ParseVariableString, count, $state, i18n, moment) {
        var runTimeElapsedTimer = null;
        let workflowMakerNodeIdCounter = 1;
        let nodeIdToMakerIdMapping = {};
        let chartNodeIdToIndexMapping = {};

        var getLinks = function() {
            var getLink = function(key) {
                if(key === 'schedule') {
                    if($scope.workflow.related.schedule) {
                        return '/#/templates/workflow_job_template/' + $scope.workflow.workflow_job_template + '/schedules' + $scope.workflow.related.schedule.split(/api\/v\d+\/schedules/)[1];
                    }
                    else {
                        return null;
                    }
                }
                else {
                    if ($scope.workflow.related[key]) {
                        return '/#/' + $scope.workflow.related[key]
                            .split(/api\/v\d+\//)[1];
                    } else {
                        return null;
                    }
                }
            };

            $scope.workflow_template_link = '/#/templates/workflow_job_template/'+$scope.workflow.workflow_job_template;
            $scope.created_by_link = getLink('created_by');
            $scope.scheduled_by_link = getLink('schedule');
            $scope.cloud_credential_link = getLink('cloud_credential');
            $scope.network_credential_link = getLink('network_credential');

            if ($scope.workflow.summary_fields.inventory) {
                if ($scope.workflow.summary_fields.inventory.kind === 'smart') {
                    $scope.inventory_link = '/#/inventories/smart/' + $scope.workflow.inventory;
                } else {
                    $scope.inventory_link = '/#/inventories/inventory/' + $scope.workflow.inventory;
                }
            }

            $scope.strings = {
                tooltips: {
                    RELAUNCH: i18n._('Relaunch using the same parameters'),
                    CANCEL: i18n._('Cancel'),
                    DELETE: i18n._('Delete'),
                    EDIT_USER: i18n._('Edit the user'),
                    EDIT_WORKFLOW: i18n._('Edit the workflow job template'),
                    EDIT_SLICE_TEMPLATE: i18n._('Edit the slice job template'),
                    EDIT_SCHEDULE: i18n._('Edit the schedule'),
                    SOURCE_WORKFLOW_JOB: i18n._('View the source Workflow Job'),
                    TOGGLE_STDOUT_FULLSCREEN: i18n._('Expand Output'),
                    STATUS: '' // re-assigned elsewhere
                },
                labels: {
                    TEMPLATE: i18n._('Template'),
                    LAUNCHED_BY: i18n._('Launched By'),
                    STARTED: i18n._('Started'),
                    FINISHED: i18n._('Finished'),
                    LABELS: i18n._('Labels'),
                    STATUS: i18n._('Status'),
                    SLICE_TEMPLATE: i18n._('Slice Job Template'),
                    JOB_EXPLANATION: i18n._('Explanation'),
                    SOURCE_WORKFLOW_JOB: i18n._('Source Workflow'),
                    INVENTORY: i18n._('Inventory')
                },
                details: {
                    HEADER: i18n._('DETAILS'),
                    NOT_FINISHED: i18n._('Not Finished'),
                    NOT_STARTED: i18n._('Not Started'),
                    SHOW_LESS: i18n._('Show Less'),
                    SHOW_MORE: i18n._('Show More'),
                },
                results: {
                    TOTAL_JOBS: i18n._('Total Jobs'),
                    ELAPSED: i18n._('Elapsed'),
                },
                legend: {
                    ON_SUCCESS: i18n._('On Success'),
                    ON_FAILURE: i18n._('On Failure'),
                    ALWAYS: i18n._('Always'),
                    PROJECT_SYNC: i18n._('Project Sync'),
                    INVENTORY_SYNC: i18n._('Inventory Sync'),
                    WORKFLOW: i18n._('Workflow'),
                    KEY: i18n._('KEY'),
                }
            };
        };

        var getLabelsAndTooltips = function() {
            var getLabel = function(key) {
                if ($scope.workflowOptions && $scope.workflowOptions[key]) {
                    return $scope.workflowOptions[key].choices
                        .filter(val => val[0] === $scope.workflow[key])
                        .map(val => val[1])[0];
                } else {
                    return null;
                }
            };

            $scope.workflow.statusLabel = i18n._(getLabel('status'));
            $scope.strings.tooltips.STATUS = `${i18n._('Job')} ${$scope.workflow.statusLabel}`;
        };

        var updateWorkflowJobElapsedTimer = function(time) {
            $scope.workflow.elapsed = time;
        };

        function init() {
            // put initially resolved request data on scope
            $scope.workflow = workflowData;
            $scope.workflow_nodes = workflowNodes;
            $scope.workflowOptions = workflowDataOptions.actions.GET;
            $scope.labels = jobLabels;
            $scope.showManualControls = false;
            $scope.readOnly = true;

            // Start elapsed time updater for job known to be running
            if ($scope.workflow.started !== null && $scope.workflow.status === 'running') {
                runTimeElapsedTimer = workflowResultsService.createOneSecondTimer($scope.workflow.started, updateWorkflowJobElapsedTimer);
            }

            if(workflowData.summary_fields && workflowData.summary_fields.workflow_job_template &&
                workflowData.summary_fields.workflow_job_template.id){
                    $scope.workflow_job_template_link = `/#/templates/workflow_job_template/${$scope.workflow.summary_fields.workflow_job_template.id}`;
            }

            if(workflowData.summary_fields && workflowData.summary_fields.job_template &&
                workflowData.summary_fields.job_template.id){
                    $scope.slice_job_template_link = `/#/templates/job_template/${$scope.workflow.summary_fields.job_template.id}`;
            }

            if (_.get(workflowData, 'summary_fields.source_workflow_job.id')) {
                $scope.source_workflow_job_link = `/#/workflows/${workflowData.summary_fields.source_workflow_job.id}`;
            }

            if (workflowData.job_explanation) {
                const limit = 150;
                const more = workflowData.job_explanation;
                const less = $filter('limitTo')(more, limit);
                const showMore = false;
                const hasMoreToShow = more.length > limit;

                const job_explanation = {
                    more: more,
                    less: less,
                    showMore: showMore,
                    hasMoreToShow: hasMoreToShow
                };

                $scope.job_explanation = job_explanation;
            }

            // turn related api browser routes into front end routes
            getLinks();

            // use options labels to manipulate display of details
            getLabelsAndTooltips();

            // set up a read only code mirror for extra vars
            $scope.variables = ParseVariableString($scope.workflow.extra_vars);
            $scope.parseType = 'yaml';
            $scope.varsTooltip= i18n._('Read only view of extra variables added to the workflow.');
            $scope.varsLabel = i18n._('Extra Variables');

            // Click binding for the expand/collapse button on the standard out log
            $scope.stdoutFullScreen = false;

            let nonRootNodeIds = [];
            let allNodeIds = [];
            let arrayOfLinksForChart = [];
            let arrayOfNodesForChart = [
                {
                    index: 0,
                    id: workflowMakerNodeIdCounter,
                    isStartNode: true,
                    unifiedJobTemplate: {
                        name: "START"
                    },
                    fixed: true,
                    x: 0,
                    y: 0
                }
            ];

            workflowMakerNodeIdCounter++;
            // Assign each node an ID - 0 is reserved for the start node.  We need to
            // make sure that we have an ID on every node including new nodes so the
            // ID returned by the api won't do
            workflowNodes.forEach((node) => {
                node.workflowMakerNodeId = workflowMakerNodeIdCounter;
                const nodeObj = {
                    index: workflowMakerNodeIdCounter-1,
                    id: workflowMakerNodeIdCounter,
                    unifiedJobTemplate: node.summary_fields.unified_job_template
                };
                if(node.summary_fields.job) {
                    nodeObj.job = node.summary_fields.job;
                }
                if(node.summary_fields.unified_job_template) {
                    nodeObj.unifiedJobTemplate = node.summary_fields.unified_job_template;
                }
                arrayOfNodesForChart.push(nodeObj);
                allNodeIds.push(node.id);
                nodeIdToMakerIdMapping[node.id] = node.workflowMakerNodeId;
                chartNodeIdToIndexMapping[workflowMakerNodeIdCounter] = workflowMakerNodeIdCounter-1;
                workflowMakerNodeIdCounter++;
            });

            workflowNodes.forEach((node) => {
                const sourceIndex = chartNodeIdToIndexMapping[node.workflowMakerNodeId];
                node.success_nodes.forEach((nodeId) => {
                    const targetIndex = chartNodeIdToIndexMapping[nodeIdToMakerIdMapping[nodeId]];
                    arrayOfLinksForChart.push({
                        source: arrayOfNodesForChart[sourceIndex],
                        target: arrayOfNodesForChart[targetIndex],
                        edgeType: "success"
                    });
                    nonRootNodeIds.push(nodeId);
                });
                node.failure_nodes.forEach((nodeId) => {
                    const targetIndex = chartNodeIdToIndexMapping[nodeIdToMakerIdMapping[nodeId]];
                    arrayOfLinksForChart.push({
                        source: arrayOfNodesForChart[sourceIndex],
                        target: arrayOfNodesForChart[targetIndex],
                        edgeType: "failure"
                    });
                    nonRootNodeIds.push(nodeId);
                });
                node.always_nodes.forEach((nodeId) => {
                    const targetIndex = chartNodeIdToIndexMapping[nodeIdToMakerIdMapping[nodeId]];
                    arrayOfLinksForChart.push({
                        source: arrayOfNodesForChart[sourceIndex],
                        target: arrayOfNodesForChart[targetIndex],
                        edgeType: "always"
                    });
                    nonRootNodeIds.push(nodeId);
                });
            });

            let uniqueNonRootNodeIds = Array.from(new Set(nonRootNodeIds));

            let rootNodes = _.difference(allNodeIds, uniqueNonRootNodeIds);

            rootNodes.forEach((rootNodeId) => {
                const targetIndex = chartNodeIdToIndexMapping[nodeIdToMakerIdMapping[rootNodeId]];
                arrayOfLinksForChart.push({
                    source: arrayOfNodesForChart[0],
                    target: arrayOfNodesForChart[targetIndex],
                    edgeType: "always"
                });
            });

            $scope.treeState = { arrayOfNodesForChart, arrayOfLinksForChart };

        }

        $scope.toggleStdoutFullscreen = function() {

            $scope.$broadcast('workflowDetailsResized');

            $scope.stdoutFullScreen = !$scope.stdoutFullScreen;

            if ($scope.stdoutFullScreen === true) {
                $scope.toggleStdoutFullscreenTooltip = i18n._("Collapse Output");
            } else if ($scope.stdoutFullScreen === false) {
                $scope.toggleStdoutFullscreenTooltip = i18n._("Expand Output");
            }
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

        $scope.toggleManualControls = function() {
            $scope.showManualControls = !$scope.showManualControls;
        };

        $scope.lessLabels = false;
        $scope.toggleLessLabels = function() {
            if (!$scope.lessLabels) {
                $('#workflow-results-labels').slideUp(200);
                $scope.lessLabels = true;
            }
            else {
                $('#workflow-results-labels').slideDown(200);
                $scope.lessLabels = false;
            }
        };

        $scope.panChart = function(direction) {
            $scope.$broadcast('panWorkflowChart', {
                direction: direction
            });
        };

        $scope.zoomChart = function(zoom) {
            $scope.$broadcast('zoomWorkflowChart', {
                zoom: zoom
            });
        };

        $scope.resetChart = function() {
            $scope.$broadcast('resetWorkflowChart');
        };

        $scope.zoomToFitChart = function() {
            $scope.$broadcast('zoomToFitChart');
        };

        $scope.workflowZoomed = function(zoom) {
            $scope.$broadcast('workflowZoomed', {
                zoom: zoom
            });
        };

        init();

        // Processing of job-status messages from the websocket
        $scope.$on(`ws-jobs`, function(e, data) {
            // Update the workflow job's unified job:
            if (parseInt(data.unified_job_id, 10) === parseInt($scope.workflow.id,10)) {
                    $scope.workflow.status = data.status;
                    // start internval counter for job that transitioned to running
                    if ($scope.workflow.status === 'running') {
                        runTimeElapsedTimer = workflowResultsService.createOneSecondTimer(moment(), updateWorkflowJobElapsedTimer);
                    }

                    if(data.status === "successful" || data.status === "failed" || data.status === "canceled" || data.status === "error"){
                        $state.go('.', null, { reload: true });
                    }
            }
            // Update the jobs spawned by the workflow:
            if(data.hasOwnProperty('workflow_job_id') &&
                parseInt(data.workflow_job_id, 10) === parseInt($scope.workflow.id,10)){

                    // This check ensures that the workflow status icon doesn't get stuck in
                    // the waiting state due to the UI missing the initial socket message.  This
                    // can happen if the GET request on the workflow job returns "waiting" and
                    // the sockets aren't established yet so we miss the event that indicates
                    // the workflow job has moved into a running state.
                    if (!_.includes(['running', 'successful', 'failed', 'error', 'canceled'], $scope.workflow.status)){
                        $scope.workflow.status = 'running';
                        runTimeElapsedTimer = workflowResultsService.createOneSecondTimer(moment(), updateWorkflowJobElapsedTimer);
                    }

                    $scope.treeState.arrayOfNodesForChart[chartNodeIdToIndexMapping[nodeIdToMakerIdMapping[data.workflow_node_id]]].job = {
                        id: data.unified_job_id,
                        status: data.status
                    };


                    $scope.workflow_nodes.forEach(node => {
                        if(parseInt(node.id) === parseInt(data.workflow_node_id)){
                            node.summary_fields.job = {
                                    status: data.status
                            };
                        }
                    });

                    $scope.$broadcast("refreshWorkflowChart");
            }
            getLabelsAndTooltips();
        });

        $scope.$on('$destroy', function() {
            workflowResultsService.destroyTimer(runTimeElapsedTimer);
        });
}];
