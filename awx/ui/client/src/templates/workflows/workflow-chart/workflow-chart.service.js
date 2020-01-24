export default [function(){
    return {
        generateArraysOfNodesAndLinks: (allNodes) => {
            let nonRootNodeIds = [];
            let allNodeIds = [];
            let arrayOfLinksForChart = [];
            let nodeIdToChartNodeIdMapping = {};
            let chartNodeIdToIndexMapping = {};
            let nodeRef = {};
            let nodeIdCounter = 1;
            let arrayOfNodesForChart = [
                {
                    id: nodeIdCounter,
                    unifiedJobTemplate: {
                        name: "START"
                    }
                }
            ];
            nodeIdCounter++;
            // Assign each node an ID - 0 is reserved for the start node.  We need to
            // make sure that we have an ID on every node including new nodes so the
            // ID returned by the api won't do
            allNodes.forEach((node) => {
                node.workflowMakerNodeId = nodeIdCounter;
                nodeRef[nodeIdCounter] = {
                    originalNodeObject: node
                };

                const nodeObj = {
                    index: nodeIdCounter-1,
                    id: nodeIdCounter,
                    all_parents_must_converge: node.all_parents_must_converge,
                };

                if(node.summary_fields.job) {
                    nodeObj.job = node.summary_fields.job;
                }
                if(node.summary_fields.unified_job_template) {
                    nodeRef[nodeIdCounter].unifiedJobTemplate = nodeObj.unifiedJobTemplate = node.summary_fields.unified_job_template;
                }

                arrayOfNodesForChart.push(nodeObj);
                allNodeIds.push(node.id);
                nodeIdToChartNodeIdMapping[node.id] = node.workflowMakerNodeId;
                chartNodeIdToIndexMapping[nodeIdCounter] = nodeIdCounter-1;
                nodeIdCounter++;
            });

            allNodes.forEach((node) => {
                const sourceIndex = chartNodeIdToIndexMapping[node.workflowMakerNodeId];
                node.success_nodes.forEach((nodeId) => {
                    const targetIndex = chartNodeIdToIndexMapping[nodeIdToChartNodeIdMapping[nodeId]];
                    arrayOfLinksForChart.push({
                        source: arrayOfNodesForChart[sourceIndex],
                        target: arrayOfNodesForChart[targetIndex],
                        edgeType: "success"
                    });
                    nonRootNodeIds.push(nodeId);
                });
                node.failure_nodes.forEach((nodeId) => {
                    const targetIndex = chartNodeIdToIndexMapping[nodeIdToChartNodeIdMapping[nodeId]];
                    arrayOfLinksForChart.push({
                        source: arrayOfNodesForChart[sourceIndex],
                        target: arrayOfNodesForChart[targetIndex],
                        edgeType: "failure"
                    });
                    nonRootNodeIds.push(nodeId);
                });
                node.always_nodes.forEach((nodeId) => {
                    const targetIndex = chartNodeIdToIndexMapping[nodeIdToChartNodeIdMapping[nodeId]];
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
                const targetIndex = chartNodeIdToIndexMapping[nodeIdToChartNodeIdMapping[rootNodeId]];
                arrayOfLinksForChart.push({
                    source: arrayOfNodesForChart[0],
                    target: arrayOfNodesForChart[targetIndex],
                    edgeType: "always"
                });
            });

            return {
                arrayOfNodesForChart,
                arrayOfLinksForChart,
                nodeIdToChartNodeIdMapping,
                nodeRef,
                workflowMakerNodeIdCounter: nodeIdCounter
            };
        }
    };
}];
