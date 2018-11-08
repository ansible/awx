export default [function(){
    return {
        generateDepthMap: (arrayOfLinks) => {
            let depthMap = {};
            let nodesWithChildren = {};

            let walkBranch = (nodeId, depth) => {
                depthMap[nodeId] = depthMap[nodeId] ? (depth > depthMap[nodeId] ? depth : depthMap[nodeId]) : depth;
                if (nodesWithChildren[nodeId]) {
                    _.forEach(nodesWithChildren[nodeId].children, (childNodeId) => {
                        walkBranch(childNodeId, depth+1);
                    });
                }
            };

            let rootNodeIds = [];
            arrayOfLinks.forEach(link => {
                // link.source.index of 0 is our artificial start node
                if (link.source.index !== 0) {
                    if (!nodesWithChildren[link.source.id]) {
                        nodesWithChildren[link.source.id] = {
                            children: []
                        };
                    }

                    nodesWithChildren[link.source.id].children.push(link.target.id);
                } else {
                    // Store the fact that might be a root node
                    rootNodeIds.push(link.target.id);
                }
            });

            _.forEach(rootNodeIds, function(rootNodeId) {
                walkBranch(rootNodeId, 1);
                depthMap[rootNodeId] = 1;
            });

            return depthMap;
        },
        generateArraysOfNodesAndLinks: function(allNodes) {
            let nonRootNodeIds = [];
            let allNodeIds = [];
            let arrayOfLinksForChart = [];
            let nodeIdToChartNodeIdMapping = {};
            let chartNodeIdToIndexMapping = {};
            let nodeRef = {};
            let nodeIdCounter = 1;
            let arrayOfNodesForChart = [
                {
                    index: 0,
                    id: nodeIdCounter,
                    isStartNode: true,
                    unifiedJobTemplate: {
                        name: "START"
                    },
                    fixed: true,
                    x: 0,
                    y: 0
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
                    id: nodeIdCounter
                };

                if(node.summary_fields.job) {
                    nodeObj.job = node.summary_fields.job;
                }
                if(node.summary_fields.unified_job_template) {
                    nodeObj.unifiedJobTemplate = node.summary_fields.unified_job_template;
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
                chartNodeIdToIndexMapping,
                nodeIdToChartNodeIdMapping,
                nodeRef,
                workflowMakerNodeIdCounter: nodeIdCounter
            };
        }
    };
}];
