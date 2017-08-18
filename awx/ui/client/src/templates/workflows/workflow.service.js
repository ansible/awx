export default ['$q', function($q){
    return {
        searchTree: function(params) {
            // params.element
            // params.matchingId
            // params.byNodeId

            let prospectiveId = params.byNodeId ? params.element.nodeId : params.element.id;

            if(prospectiveId === params.matchingId){
                 return params.element;
            }else if (params.element.children && params.element.children.length > 0){
                 let result = null;
                 const thisService = this;
                 _.forEach(params.element.children, function(child) {
                     result = thisService.searchTree({
                         element: child,
                         matchingId: params.matchingId,
                         byNodeId: params.byNodeId ? params.byNodeId : false
                     });
                     if(result) {
                         return false;
                     }
                 });
                 return result;
            }
            return null;
        },
        removeNodeFromTree: function(params) {
            // params.tree
            // params.nodeToBeDeleted

            let parentNode = this.searchTree({
                element: params.tree,
                matchingId: params.nodeToBeDeleted.parent.id
            });
            let nodeToBeDeleted = this.searchTree({
                element: parentNode,
                matchingId: params.nodeToBeDeleted.id
            });

            if(nodeToBeDeleted.children) {
                _.forEach(nodeToBeDeleted.children, function(child) {
                    if(nodeToBeDeleted.isRoot) {
                        child.isRoot = true;
                        child.edgeType = "always";
                    }
                    child.parent = parentNode;
                    parentNode.children.push(child);
                });
            }

            _.forEach(parentNode.children, function(child, index) {
                if(child.id === params.nodeToBeDeleted.id) {
                    parentNode.children.splice(index, 1);
                    return false;
                }
            });
        },
        addPlaceholderNode: function(params) {
            // params.parent
            // params.betweenTwoNodes
            // params.tree
            // params.id

            let placeholder = {
                children: [],
                c: "#D7D7D7",
                id: params.id,
                canDelete: true,
                canEdit: false,
                canAddTo: true,
                placeholder: true,
                isNew: true,
                edited: false,
                isRoot: params.parent.isStartNode ? true : false
            };

            let parentNode = (params.betweenTwoNodes) ? this.searchTree({element: params.tree, matchingId: params.parent.source.id}) : this.searchTree({element: params.tree, matchingId: params.parent.id});
            let placeholderRef;

            if(params.betweenTwoNodes) {
                _.forEach(parentNode.children, function(child, index) {
                    if(child.id === params.parent.target.id) {
                        placeholder.children.push(child);
                        parentNode.children[index] = placeholder;
                        placeholderRef = parentNode.children[index];
                        child.parent = parentNode.children[index];
                        return false;
                    }
                });
            }
            else {
                if(parentNode.children) {
                    parentNode.children.push(placeholder);
                    placeholderRef = parentNode.children[parentNode.children.length - 1];
                } else {
                    parentNode.children = [placeholder];
                    placeholderRef = parentNode.children[0];
                }
            }

            return placeholderRef;
        },
        getSiblingConnectionTypes: function(params) {
            // params.parentId
            // params.childId
            // params.tree

            let siblingConnectionTypes = {};

            let parentNode = this.searchTree({
                element: params.tree,
                matchingId: params.parentId
            });

            if(parentNode.children && parentNode.children.length > 0) {
                // Loop across them and add the types as keys to siblingConnectionTypes
                _.forEach(parentNode.children, function(child) {
                    if(child.id !== params.childId && !child.placeholder && child.edgeType) {
                        siblingConnectionTypes[child.edgeType] = true;
                    }
                });
            }

            return Object.keys(siblingConnectionTypes);
        },
        buildTree: function(params) {
            //params.workflowNodes

            let deferred = $q.defer();

            let _this = this;

            let treeData = {
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

            let nodesArray = params.workflowNodes;
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
                let branch = _this.buildBranch({
                    nodeId: rootNodeId,
                    edgeType: "always",
                    nodesObj: nodesObj,
                    isRoot: true,
                    treeData: treeData
                });

                treeData.data.children.push(branch);
            });

            deferred.resolve(treeData);

            return deferred.promise;
        },
        buildBranch: function(params) {
            // params.nodeId
            // params.parentId
            // params.edgeType
            // params.nodesObj
            // params.isRoot
            // params.treeData

            let _this = this;

            let treeNode = {
                children: [],
                c: "#D7D7D7",
                id: params.treeData.nextIndex,
                nodeId: params.nodeId,
                canDelete: true,
                canEdit: true,
                canAddTo: true,
                placeholder: false,
                edgeType: params.edgeType,
                isNew: false,
                edited: false,
                originalEdge: params.edgeType,
                originalNodeObj: _.clone(params.nodesObj[params.nodeId]),
                promptValues: {},
                isRoot: params.isRoot ? params.isRoot : false
            };

            params.treeData.data.totalNodes++;

            params.treeData.nextIndex++;

            if(params.parentId) {
                treeNode.originalParentId = params.parentId;
            }

            if(params.nodesObj[params.nodeId].summary_fields) {
                if(params.nodesObj[params.nodeId].summary_fields.job) {
                    treeNode.job = _.clone(params.nodesObj[params.nodeId].summary_fields.job);
                }

                if(params.nodesObj[params.nodeId].summary_fields.unified_job_template) {
                    treeNode.unifiedJobTemplate = _.clone(params.nodesObj[params.nodeId].summary_fields.unified_job_template);
                }
            }

            // Loop across the success nodes and add them recursively
            _.forEach(params.nodesObj[params.nodeId].success_nodes, function(successNodeId) {
                treeNode.children.push(_this.buildBranch({
                    nodeId: successNodeId,
                    parentId: params.nodeId,
                    edgeType: "success",
                    nodesObj: params.nodesObj,
                    treeData: params.treeData
                }));
            });

            // failure nodes
            _.forEach(params.nodesObj[params.nodeId].failure_nodes, function(failureNodesId) {
                treeNode.children.push(_this.buildBranch({
                    nodeId: failureNodesId,
                    parentId: params.nodeId,
                    edgeType: "failure",
                    nodesObj: params.nodesObj,
                    treeData: params.treeData
                }));
            });

            // always nodes
            _.forEach(params.nodesObj[params.nodeId].always_nodes, function(alwaysNodesId) {
                treeNode.children.push(_this.buildBranch({
                    nodeId: alwaysNodesId,
                    parentId: params.nodeId,
                    edgeType: "always",
                    nodesObj: params.nodesObj,
                    treeData: params.treeData
                }));
            });

            return treeNode;
        },
        updateStatusOfNode: function(params) {
            // params.treeData
            // params.nodeId
            // params.status

            let matchingNode = this.searchTree({
                element: params.treeData.data,
                matchingId: params.nodeId,
                byNodeId: true
            });

            if(matchingNode) {
                matchingNode.job = {
                    status: params.status,
                    id: params.unified_job_id
                };
            }

        },
        checkForEdgeConflicts: function(params) {
            //params.treeData
            //params.edgeFlags

            let hasAlways = false;
            let hasSuccessFailure = false;
            let _this = this;

            _.forEach(params.treeData.children, function(child) {
                // Flip the flag to false for now - we'll set it to true later on
                // if we detect a conflict
                child.edgeConflict = false;
                if(child.edgeType === 'always') {
                    hasAlways = true;
                }
                else if(child.edgeType === 'success' || child.edgeType === 'failure') {
                    hasSuccessFailure = true;
                }

                _this.checkForEdgeConflicts({
                    treeData: child,
                    edgeFlags: params.edgeFlags
                });
            });

            if(hasAlways && hasSuccessFailure) {
                // We have a conflict
                _.forEach(params.treeData.children, function(child) {
                    child.edgeConflict = true;
                });

                params.edgeFlags.conflict = true;
            }
        }
    };
}];
