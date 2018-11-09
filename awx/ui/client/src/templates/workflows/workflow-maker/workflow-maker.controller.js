/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'TemplatesService',
    'ProcessErrors', 'CreateSelect2', '$q', 'JobTemplateModel',
    'Empty', 'PromptService', 'Rest', 'TemplatesStrings', 'WorkflowChartService',
    function ($scope, TemplatesService,
        ProcessErrors, CreateSelect2, $q, JobTemplate,
        Empty, PromptService, Rest, TemplatesStrings, WorkflowChartService) {

        $scope.strings = TemplatesStrings;
        $scope.preventCredsWithPasswords = true;

        let deletedNodeIds = [];
        let workflowMakerNodeIdCounter = 1;
        let nodeIdToChartNodeIdMapping = {};
        let chartNodeIdToIndexMapping = {};
        let nodeRef = {};

        $scope.showKey = false;
        $scope.toggleKey = () => $scope.showKey = !$scope.showKey;
        $scope.keyClassList = `{ 'Key-menuIcon--active': showKey }`;

        $scope.readOnly = !_.get($scope, 'workflowJobTemplateObj.summary_fields.user_capabilities.edit');

        $scope.formState = {
            'showNodeForm': false,
            'showLinkForm': false
        };

        let buildSendableNodeData = function (node) {
            // Create the node
            let sendableNodeData = {
                extra_data: {},
                inventory: null,
                job_type: null,
                job_tags: null,
                skip_tags: null,
                limit: null,
                diff_mode: null,
                verbosity: null,
                credential: null
            };

            if (_.has(node, 'fullUnifiedJobTemplateObject')) {
                sendableNodeData.unified_job_template = node.fullUnifiedJobTemplateObject.id;
            }

            if (_.has(node, 'promptData.extraVars')) {
                if (_.get(node, 'promptData.launchConf.defaults.extra_vars')) {
                    const defaultVars = jsyaml.safeLoad(node.promptData.launchConf.defaults.extra_vars);

                    // Only include extra vars that differ from the template default vars
                    _.forOwn(node.promptData.extraVars, (value, key) => {
                        if (!defaultVars[key] || defaultVars[key] !== value) {
                            sendableNodeData.extra_data[key] = value;
                        }
                    });
                    if (_.isEmpty(sendableNodeData.extra_data)) {
                        delete sendableNodeData.extra_data;
                    }
                } else {
                    if (_.has(node, 'promptData.extraVars') && !_.isEmpty(node.promptData.extraVars)) {
                        sendableNodeData.extra_data = node.promptData.extraVars;
                    }
                }
            }

            // Check to see if the user has provided any prompt values that are different
            // from the defaults in the job template

            if (_.has(node, 'fullUnifiedJobTemplateObject') && node.fullUnifiedJobTemplateObject.type === "job_template" && node.promptData) {
                sendableNodeData = PromptService.bundlePromptDataForSaving({
                    promptData: node.promptData,
                    dataToSave: sendableNodeData
                });
            }

            return sendableNodeData;
        };

        $scope.closeWorkflowMaker = function() {
            // Revert the data to the master which was created when the dialog was opened
            $scope.graphState.nodeTree = angular.copy($scope.graphStateMaster);
            $scope.closeDialog();
        };

        $scope.saveWorkflowMaker = function () {

            if ($scope.graphState.arrayOfNodesForChart.length > 1) {
                let addPromises = [];
                let editPromises = [];
                let credentialsToPost = [];

                Object.keys(nodeRef).map((workflowMakerNodeId) => {
                    if (nodeRef[workflowMakerNodeId].isNew) {
                        addPromises.push(TemplatesService.addWorkflowNode({
                            url: $scope.workflowJobTemplateObj.related.workflow_nodes,
                            data: buildSendableNodeData(nodeRef[workflowMakerNodeId])
                        }).then(({data}) => {
                            nodeRef[workflowMakerNodeId].originalNodeObject = data;
                            nodeIdToChartNodeIdMapping[data.id] = parseInt(workflowMakerNodeId);
                            if (_.get(nodeRef[workflowMakerNodeId], 'promptData.launchConf.ask_credential_on_launch')) {
                                // This finds the credentials that were selected in the prompt but don't occur
                                // in the template defaults
                                let credentialIdsToPost = nodeRef[workflowMakerNodeId].promptData.prompts.credentials.value.filter(function (credFromPrompt) {
                                    let defaultCreds = _.get(nodeRef[workflowMakerNodeId], 'promptData.launchConf.defaults.credentials', []);
                                    return !defaultCreds.some(function (defaultCred) {
                                        return credFromPrompt.id === defaultCred.id;
                                    });
                                });

                                credentialIdsToPost.forEach((credentialToPost) => {
                                    credentialsToPost.push({
                                        id: data.id,
                                        data: {
                                            id: credentialToPost.id
                                        }
                                    });
                                });
                            }
                        }));
                    } else if (nodeRef[workflowMakerNodeId].isEdited) {
                        editPromises.push(TemplatesService.editWorkflowNode({
                            id: nodeRef[workflowMakerNodeId].originalNodeObject.id,
                            data: buildSendableNodeData(nodeRef[workflowMakerNodeId])
                        }));
                    }

                });

                let deletePromises = deletedNodeIds.map(function (nodeId) {
                    return TemplatesService.deleteWorkflowJobTemplateNode(nodeId);
                });

                $q.all(addPromises.concat(editPromises, deletePromises))
                    .then(() => {
                        let disassociatePromises = [];
                        let associatePromises = [];
                        let linkMap = {};

                        // Build a link map for easy access
                        $scope.graphState.arrayOfLinksForChart.forEach(link => {
                            // link.source.id of 1 is our artificial start node
                            if (link.source.id !== 1) {
                                const sourceNodeId = nodeRef[link.source.id].originalNodeObject.id;
                                const targetNodeId = nodeRef[link.target.id].originalNodeObject.id;
                                if (!linkMap[sourceNodeId]) {
                                    linkMap[sourceNodeId] = {};
                                }

                                linkMap[sourceNodeId][targetNodeId] = link.edgeType;
                            }
                        });

                        Object.keys(nodeRef).map((workflowNodeId) => {
                            let nodeId = nodeRef[workflowNodeId].originalNodeObject.id;
                            if (nodeRef[workflowNodeId].originalNodeObject.success_nodes) {
                                nodeRef[workflowNodeId].originalNodeObject.success_nodes.forEach((successNodeId) => {
                                    if (
                                        !deletedNodeIds.includes(successNodeId) &&
                                        (!linkMap[nodeId] ||
                                        !linkMap[nodeId][successNodeId] ||
                                        linkMap[nodeId][successNodeId] !== "success")
                                    ) {
                                        disassociatePromises.push(
                                            TemplatesService.disassociateWorkflowNode({
                                                parentId: nodeId,
                                                nodeId: successNodeId,
                                                edge: "success"
                                            })
                                        );
                                    }
                                });
                            }
                            if (nodeRef[workflowNodeId].originalNodeObject.failure_nodes) {
                                nodeRef[workflowNodeId].originalNodeObject.failure_nodes.forEach((failureNodeId) => {
                                    if (
                                        !deletedNodeIds.includes(failureNodeId) &&
                                        (!linkMap[nodeId] ||
                                        !linkMap[nodeId][failureNodeId] ||
                                        linkMap[nodeId][failureNodeId] !== "failure")
                                    ) {
                                        disassociatePromises.push(
                                            TemplatesService.disassociateWorkflowNode({
                                                parentId: nodeId,
                                                nodeId: failureNodeId,
                                                edge: "failure"
                                            })
                                        );
                                    }
                                });
                            }
                            if (nodeRef[workflowNodeId].originalNodeObject.always_nodes) {
                                nodeRef[workflowNodeId].originalNodeObject.always_nodes.forEach((alwaysNodeId) => {
                                    if (
                                        !deletedNodeIds.includes(alwaysNodeId) &&
                                        (!linkMap[nodeId] ||
                                        !linkMap[nodeId][alwaysNodeId] ||
                                        linkMap[nodeId][alwaysNodeId] !== "always")
                                    ) {
                                        disassociatePromises.push(
                                            TemplatesService.disassociateWorkflowNode({
                                                parentId: nodeId,
                                                nodeId: alwaysNodeId,
                                                edge: "always"
                                            })
                                        );
                                    }
                                });
                            }
                        });

                        Object.keys(linkMap).map((sourceNodeId) => {
                            Object.keys(linkMap[sourceNodeId]).map((targetNodeId) => {
                                const sourceChartNodeId = nodeIdToChartNodeIdMapping[sourceNodeId];
                                const targetChartNodeId = nodeIdToChartNodeIdMapping[targetNodeId];
                                switch(linkMap[sourceNodeId][targetNodeId]) {
                                    case "success":
                                        if (
                                            !nodeRef[sourceChartNodeId].originalNodeObject.success_nodes ||
                                            !nodeRef[sourceChartNodeId].originalNodeObject.success_nodes.includes(nodeRef[targetChartNodeId].id)
                                        ) {
                                            associatePromises.push(
                                                TemplatesService.associateWorkflowNode({
                                                    parentId: parseInt(sourceNodeId),
                                                    nodeId: parseInt(targetNodeId),
                                                    edge: "success"
                                                })
                                            );
                                        }
                                        break;
                                    case "failure":
                                        if (
                                            !nodeRef[sourceChartNodeId].originalNodeObject.failure_nodes ||
                                            !nodeRef[sourceChartNodeId].originalNodeObject.failure_nodes.includes(nodeRef[targetChartNodeId].id)
                                        ) {
                                            associatePromises.push(
                                                TemplatesService.associateWorkflowNode({
                                                    parentId: parseInt(sourceNodeId),
                                                    nodeId: parseInt(targetNodeId),
                                                    edge: "failure"
                                                })
                                            );
                                        }
                                        break;
                                    case "always":
                                        if (
                                            !nodeRef[sourceChartNodeId].originalNodeObject.always_nodes ||
                                            !nodeRef[sourceChartNodeId].originalNodeObject.always_nodes.includes(nodeRef[targetChartNodeId].id)
                                        ) {
                                            associatePromises.push(
                                                TemplatesService.associateWorkflowNode({
                                                    parentId: parseInt(sourceNodeId),
                                                    nodeId: parseInt(targetNodeId),
                                                    edge: "always"
                                                })
                                            );
                                        }
                                        break;
                                }
                            });
                        });

                        $q.all(disassociatePromises)
                            .then(function () {
                                let credentialPromises = credentialsToPost.map(function (request) {
                                    return TemplatesService.postWorkflowNodeCredential({
                                        id: request.id,
                                        data: request.data
                                    });
                                });

                                return $q.all(associatePromises.concat(credentialPromises))
                                    .then(function () {
                                        $scope.closeDialog();
                                    });
                            }).catch(({
                                data,
                                status
                            }) => {
                                ProcessErrors($scope, data, status, null, {});
                            });
                    });

            } else {

                let deletePromises = deletedNodeIds.map(function (nodeId) {
                    return TemplatesService.deleteWorkflowJobTemplateNode(nodeId);
                });

                $q.all(deletePromises)
                    .then(function () {
                        $scope.closeDialog();
                        $state.transitionTo('templates');
                    });
            }
        };

        /* ADD NODE FUNCTIONS */

        $scope.startAddNodeWithoutChild = function (parent) {
            if ($scope.nodeConfig) {
                $scope.cancelNodeForm();
            }

            $scope.graphState.arrayOfNodesForChart.push({
                index: $scope.graphState.arrayOfNodesForChart.length,
                id: workflowMakerNodeIdCounter,
                unifiedJobTemplate: null
            });

            $scope.graphState.nodeBeingAdded = workflowMakerNodeIdCounter;

            chartNodeIdToIndexMapping[workflowMakerNodeIdCounter] = $scope.graphState.arrayOfNodesForChart.length - 1;

            $scope.graphState.arrayOfLinksForChart.push({
                source: $scope.graphState.arrayOfNodesForChart[parent.index],
                target: $scope.graphState.arrayOfNodesForChart[chartNodeIdToIndexMapping[workflowMakerNodeIdCounter]],
                edgeType: "placeholder"
            });

            $scope.nodeConfig = {
                mode: "add",
                nodeId: workflowMakerNodeIdCounter,
                newNodeIsRoot: parent.index === 0
            };

            workflowMakerNodeIdCounter++;

            $scope.graphState.depthMap = WorkflowChartService.generateDepthMap($scope.graphState.arrayOfLinksForChart);

            $scope.$broadcast("refreshWorkflowChart");

            $scope.formState.showNodeForm = true;
        };

        $scope.startAddNodeWithChild = function (link) {
            if ($scope.nodeConfig) {
                $scope.cancelNodeForm();
            }

            $scope.graphState.arrayOfNodesForChart.push({
                index: $scope.graphState.arrayOfNodesForChart.length,
                id: workflowMakerNodeIdCounter,
                unifiedJobTemplate: null
            });

            $scope.graphState.nodeBeingAdded = workflowMakerNodeIdCounter;

            chartNodeIdToIndexMapping[workflowMakerNodeIdCounter] = $scope.graphState.arrayOfNodesForChart.length - 1;

            $scope.graphState.arrayOfLinksForChart.push({
                source: $scope.graphState.arrayOfNodesForChart[link.source.index],
                target: $scope.graphState.arrayOfNodesForChart[chartNodeIdToIndexMapping[workflowMakerNodeIdCounter]],
                edgeType: "placeholder"
            });

            $scope.nodeConfig = {
                mode: "add",
                nodeId: workflowMakerNodeIdCounter,
                newNodeIsRoot: link.source.id === 1
            };

            // Search for the link that used to exist between source and target and shift it to
            // go from our new node to the target
            $scope.graphState.arrayOfLinksForChart.forEach((foo) => {
                if (foo.source.id === link.source.id && foo.target.id === link.target.id) {
                    foo.source = $scope.graphState.arrayOfNodesForChart[chartNodeIdToIndexMapping[workflowMakerNodeIdCounter]];
                }
            });

            workflowMakerNodeIdCounter++;

            $scope.graphState.depthMap = WorkflowChartService.generateDepthMap($scope.graphState.arrayOfLinksForChart);

            $scope.$broadcast("refreshWorkflowChart");

            $scope.formState.showNodeForm = true;
        };

        $scope.confirmNodeForm = function(selectedTemplate, promptData, edgeType) {
            const nodeIndex = chartNodeIdToIndexMapping[$scope.nodeConfig.nodeId];
            if ($scope.nodeConfig.mode === "add") {
                if (selectedTemplate && edgeType && edgeType.value) {
                    nodeRef[$scope.nodeConfig.nodeId] = {
                        fullUnifiedJobTemplateObject: selectedTemplate,
                        promptData,
                        isNew: true
                    };

                    $scope.graphState.arrayOfNodesForChart[nodeIndex].unifiedJobTemplate = selectedTemplate;
                    $scope.graphState.nodeBeingAdded = null;

                    $scope.graphState.arrayOfLinksForChart.map( (link) => {
                        if (link.target.index === nodeIndex) {
                            link.edgeType = edgeType.value;
                        }
                    });
                }
            } else if ($scope.nodeConfig.mode === "edit") {
                if (selectedTemplate) {
                    nodeRef[$scope.nodeConfig.nodeId].fullUnifiedJobTemplateObject = selectedTemplate;
                    nodeRef[$scope.nodeConfig.nodeId].promptData = _.cloneDeep(promptData);
                    nodeRef[$scope.nodeConfig.nodeId].isEdited = true;
                    $scope.graphState.arrayOfNodesForChart[nodeIndex].unifiedJobTemplate = selectedTemplate;
                    $scope.graphState.nodeBeingEdited = null;
                }
            }

            $scope.formState.showNodeForm = false;
            $scope.nodeConfig = null;

            $scope.$broadcast("refreshWorkflowChart");
        };

        $scope.cancelNodeForm = function() {
            const nodeIndex = chartNodeIdToIndexMapping[$scope.nodeConfig.nodeId];
            if ($scope.nodeConfig.mode === "add") {
                // Remove the placeholder node from the array
                $scope.graphState.arrayOfNodesForChart.splice(nodeIndex, 1);

                // Update the links
                let parents = [];
                let children = [];

                // Remove any links that reference this node
                for( let i = $scope.graphState.arrayOfLinksForChart.length; i--; ){
                    const link = $scope.graphState.arrayOfLinksForChart[i];

                    if (link.source.index === nodeIndex || link.target.index === nodeIndex) {
                        if (link.source.index === nodeIndex) {
                            const targetIndex = link.target.index < nodeIndex ? link.target.index : link.target.index - 1;
                            children.push({index: targetIndex, edgeType: link.edgeType});
                        } else if (link.target.index === nodeIndex) {
                            const sourceIndex = link.source.index < nodeIndex ? link.source.index : link.source.index - 1;
                            parents.push(sourceIndex);
                        }
                        $scope.graphState.arrayOfLinksForChart.splice(i, 1);
                    } else {
                        if (link.source.index > nodeIndex) {
                            link.source.index--;
                        }
                        if (link.target.index > nodeIndex) {
                            link.target.index--;
                        }
                    }
                }

                // Add the new links
                parents.forEach((parentIndex) => {
                    children.forEach((child) => {
                        if (parentIndex === 0) {
                            child.edgeType = "always";
                        }
                        $scope.graphState.arrayOfLinksForChart.push({
                            source: $scope.graphState.arrayOfNodesForChart[parentIndex],
                            target: $scope.graphState.arrayOfNodesForChart[child.index],
                            edgeType: child.edgeType
                        });
                    });
                });

                delete chartNodeIdToIndexMapping[$scope.nodeConfig.nodeId];

                for (const key in chartNodeIdToIndexMapping) {
                    if (chartNodeIdToIndexMapping[key] > nodeIndex) {
                        chartNodeIdToIndexMapping[key]--;
                    }
                }

                $scope.graphState.depthMap = WorkflowChartService.generateDepthMap($scope.graphState.arrayOfLinksForChart);
            } else if ($scope.nodeConfig.mode === "edit") {
                $scope.graphState.nodeBeingEdited = null;
            }
            $scope.formState.showNodeForm = false;
            $scope.nodeConfig = null;
            $scope.$broadcast("refreshWorkflowChart");
        };

        /* EDIT NODE FUNCTIONS */

        $scope.startEditNode = function(nodeToEdit) {
            if ($scope.linkConfig) {
                $scope.cancelLinkForm();
            }

            if (!$scope.nodeConfig || ($scope.nodeConfig && $scope.nodeConfig.nodeId !== nodeToEdit.index)) {
                if ($scope.nodeConfig) {
                    $scope.cancelNodeForm();
                }

                $scope.nodeConfig = {
                    mode: "edit",
                    nodeId: nodeToEdit.id,
                    node: nodeRef[nodeToEdit.id]
                };

                $scope.graphState.nodeBeingEdited = nodeToEdit.id;

                $scope.formState.showNodeForm = true;
            }

            $scope.$broadcast("refreshWorkflowChart");
        };

        /* LINK FUNCTIONS */

        $scope.startEditLink = (linkToEdit) => {
            const setupLinkEdit = () => {

                // Determine whether or not this link can be removed
                let numberOfParents = 0;
                $scope.graphState.arrayOfLinksForChart.forEach((link) => {
                    if (link.target.id === linkToEdit.target.id) {
                        numberOfParents++;
                    }
                });

                $scope.graphState.linkBeingEdited = {
                    source: linkToEdit.source.id,
                    target: linkToEdit.target.id
                };

                $scope.linkConfig = {
                    mode: "edit",
                    parent: {
                        id: linkToEdit.source.id,
                        name: _.get(linkToEdit, 'source.unifiedJobTemplate.name') || ""
                    },
                    child: {
                        id: linkToEdit.target.id,
                        name: _.get(linkToEdit, 'target.unifiedJobTemplate.name') || ""
                    },
                    edgeType: linkToEdit.edgeType,
                    canUnlink: numberOfParents > 1
                };
                $scope.formState.showLinkForm = true;

                $scope.$broadcast("refreshWorkflowChart");
            };

            if ($scope.nodeConfig) {
                $scope.cancelNodeForm();
            }

            if ($scope.linkConfig) {
                if ($scope.linkConfig.parent.id !== linkToEdit.source.id || $scope.linkConfig.child.id !== linkToEdit.target.id) {
                    // User is going from editing one link to editing another
                    if ($scope.linkConfig.mode === "add") {
                        $scope.graphState.arrayOfLinksForChart.splice($scope.graphState.arrayOfLinksForChart.length-1, 1);
                        $scope.graphState.depthMap = WorkflowChartService.generateDepthMap($scope.graphState.arrayOfLinksForChart);
                    }
                    setupLinkEdit();
                }
            } else {
                setupLinkEdit();
            }

        };

        $scope.selectNodeForLinking = (node) => {
            if ($scope.linkConfig) {
                // This is the second node selected
                $scope.linkConfig.child = {
                    id: node.id,
                    name: node.unifiedJobTemplate.name
                };
                $scope.linkConfig.edgeType = "success";

                $scope.graphState.arrayOfNodesForChart.forEach((node) => {
                    node.isInvalidLinkTarget = false;
                });

                $scope.graphState.arrayOfLinksForChart.push({
                    target: $scope.graphState.arrayOfNodesForChart[node.index],
                    source: $scope.graphState.arrayOfNodesForChart[chartNodeIdToIndexMapping[$scope.linkConfig.parent.id]],
                    edgeType: "placeholder"
                });

                $scope.graphState.linkBeingEdited = {
                    source: $scope.graphState.arrayOfNodesForChart[node.index].id,
                    target: $scope.graphState.arrayOfNodesForChart[chartNodeIdToIndexMapping[$scope.linkConfig.parent.id]].id
                };

                $scope.graphState.arrayOfLinksForChart.forEach((link, index) => {
                    if (link.source.id === 1 && link.target.id === node.id) {
                        $scope.graphState.arrayOfLinksForChart.splice(index, 1);
                    }
                });

                $scope.graphState.depthMap = WorkflowChartService.generateDepthMap($scope.graphState.arrayOfLinksForChart);

                $scope.graphState.isLinkMode = false;
            } else {
                // This is the first node selected
                $scope.graphState.addLinkSource = node.id;
                $scope.linkConfig = {
                    mode: "add",
                    parent: {
                        id: node.id,
                        name: node.unifiedJobTemplate.name
                    }
                };

                let parentMap = {};
                let invalidLinkTargetIds = [];

                // Find and mark any ancestors as disabled to prevent cycles
                $scope.graphState.arrayOfLinksForChart.forEach((link) => {
                    // id=1 is our artificial root node so we don't care about that
                    if (link.source.id !== 1) {
                        if (link.source.id === node.id) {
                            // Disables direct children from the add link process
                            invalidLinkTargetIds.push(link.target.id);
                        }
                        if (!parentMap[link.target.id]) {
                            parentMap[link.target.id] = [];
                        }
                        parentMap[link.target.id].push(link.source.id);
                    }
                });

                let getAncestors = (id) => {
                    if (parentMap[id]) {
                        parentMap[id].forEach((parentId) => {
                            invalidLinkTargetIds.push(parentId);
                            getAncestors(parentId);
                        });
                    }
                };

                getAncestors(node.id);

                // Filter out the duplicates
                invalidLinkTargetIds.filter((element, index, array) => index === array.indexOf(element)).forEach((ancestorId) => {
                    $scope.graphState.arrayOfNodesForChart[chartNodeIdToIndexMapping[ancestorId]].isInvalidLinkTarget = true;
                });

                $scope.graphState.isLinkMode = true;

                $scope.formState.showLinkForm = true;
            }

            $scope.$broadcast("refreshWorkflowChart");
        };

        $scope.confirmLinkForm = (newEdgeType) => {
            $scope.graphState.arrayOfLinksForChart.forEach((link) => {
                if (link.source.id === $scope.linkConfig.parent.id && link.target.id === $scope.linkConfig.child.id) {
                    link.edgeType = newEdgeType;
                }
            });

            if ($scope.linkConfig.mode === "add") {
                $scope.graphState.arrayOfNodesForChart.forEach((node) => {
                    node.isInvalidLinkTarget = false;
                });
            }

            $scope.graphState.linkBeingEdited = null;
            $scope.graphState.addLinkSource = null;
            $scope.formState.showLinkForm = false;
            $scope.linkConfig = null;
            $scope.$broadcast("refreshWorkflowChart");
        };

        $scope.unlink = () => {
            // Remove the link
            for( let i = $scope.graphState.arrayOfLinksForChart.length; i--; ){
                const link = $scope.graphState.arrayOfLinksForChart[i];

                if (link.source.id === $scope.linkConfig.parent.id && link.target.id === $scope.linkConfig.child.id) {
                    $scope.graphState.arrayOfLinksForChart.splice(i, 1);
                }
            }

            $scope.graphState.depthMap = WorkflowChartService.generateDepthMap($scope.graphState.arrayOfLinksForChart);

            $scope.formState.showLinkForm = false;
            $scope.linkConfig = null;
            $scope.$broadcast("refreshWorkflowChart");
        };

        $scope.cancelLinkForm = () => {
            if ($scope.linkConfig.mode === "add" && $scope.linkConfig.child) {
                $scope.graphState.arrayOfLinksForChart.splice($scope.graphState.arrayOfLinksForChart.length-1, 1);
                let targetIsOrphaned = true;
                $scope.graphState.arrayOfLinksForChart.forEach((link) => {
                    if (link.target.id === $scope.linkConfig.child.id) {
                        targetIsOrphaned = false;
                    }
                });
                if (targetIsOrphaned) {
                    // Link it to the start node
                    $scope.graphState.arrayOfLinksForChart.push({
                        source: $scope.graphState.arrayOfNodesForChart[0],
                        target: $scope.graphState.arrayOfNodesForChart[chartNodeIdToIndexMapping[$scope.linkConfig.child.id]],
                        edgeType: "always"
                    });
                }
                $scope.graphState.depthMap = WorkflowChartService.generateDepthMap($scope.graphState.arrayOfLinksForChart);
            }
            $scope.graphState.linkBeingEdited = null;
            $scope.graphState.addLinkSource = null;
            $scope.graphState.isLinkMode = false;
            $scope.graphState.arrayOfNodesForChart.forEach((node) => {
                node.isInvalidLinkTarget = false;
            });
            $scope.formState.showLinkForm = false;
            $scope.linkConfig = null;
            $scope.$broadcast("refreshWorkflowChart");
        };

        /* DELETE NODE FUNCTIONS */

        $scope.startDeleteNode = function (nodeToDelete) {
            $scope.nodeToBeDeleted = nodeToDelete;
            $scope.deleteOverlayVisible = true;
        };

        $scope.cancelDeleteNode = function () {
            $scope.nodeToBeDeleted = null;
            $scope.deleteOverlayVisible = false;
        };

        $scope.confirmDeleteNode = function () {
            if ($scope.nodeToBeDeleted) {
                const nodeIndex = $scope.nodeToBeDeleted.index;

                if ($scope.linkBeingWorkedOn) {
                    $scope.cancelLinkForm();
                }

                // Remove the node from the array
                $scope.graphState.arrayOfNodesForChart.splice(nodeIndex, 1);

                // Update the links
                let parents = [];
                let children = [];

                // Remove any links that reference this node
                for( let i = $scope.graphState.arrayOfLinksForChart.length; i--; ){
                    const link = $scope.graphState.arrayOfLinksForChart[i];

                    if (link.source.index === nodeIndex || link.target.index === nodeIndex) {
                        if (link.source.index === nodeIndex) {
                            const targetIndex = link.target.index < nodeIndex ? link.target.index : link.target.index - 1;
                            children.push({index: targetIndex, edgeType: link.edgeType});
                        } else if (link.target.index === nodeIndex) {
                            const sourceIndex = link.source.index < nodeIndex ? link.source.index : link.source.index - 1;
                            parents.push(sourceIndex);
                        }
                        $scope.graphState.arrayOfLinksForChart.splice(i, 1);
                    } else {
                        // if (link.source.index > nodeIndex) {
                        //     link.source.index = link.source.index - 1;
                        // }
                        // if (link.target.index > nodeIndex) {
                        //     link.target.index = link.target.index - 1;
                        // }
                    }
                }

                // Add the new links
                parents.forEach((parentIndex) => {
                    children.forEach((child) => {
                        if (parentIndex === 0) {
                            child.edgeType = "always";
                        }
                        $scope.graphState.arrayOfLinksForChart.push({
                            source: $scope.graphState.arrayOfNodesForChart[parentIndex],
                            target: $scope.graphState.arrayOfNodesForChart[child.index],
                            edgeType: child.edgeType
                        });
                    });
                });

                if (nodeRef[$scope.nodeToBeDeleted.id].isNew !== true) {
                    deletedNodeIds.push(nodeRef[$scope.nodeToBeDeleted.id].originalNodeObject.id);
                }

                delete nodeRef[$scope.nodeToBeDeleted.id];

                for (const key in chartNodeIdToIndexMapping) {
                    if (chartNodeIdToIndexMapping[key] > $scope.nodeToBeDeleted.index) {
                        chartNodeIdToIndexMapping[key]--;
                    }
                }

                $scope.deleteOverlayVisible = false;

                $scope.graphState.depthMap = WorkflowChartService.generateDepthMap($scope.graphState.arrayOfLinksForChart);

                $scope.nodeToBeDeleted = null;
                $scope.deleteOverlayVisible = false;

                $scope.$broadcast("refreshWorkflowChart");
            }

        };

        $scope.toggleManualControls = function() {
            $scope.showManualControls = !$scope.showManualControls;
        };

        $scope.panChart = function (direction) {
            $scope.$broadcast('panWorkflowChart', {
                direction: direction
            });
        };

        $scope.zoomChart = function (zoom) {
            $scope.$broadcast('zoomWorkflowChart', {
                zoom: zoom
            });
        };

        $scope.resetChart = function () {
            $scope.$broadcast('resetWorkflowChart');
        };

        $scope.workflowZoomed = function (zoom) {
            $scope.$broadcast('workflowZoomed', {
                zoom: zoom
            });
        };

        $scope.zoomToFitChart = function () {
            $scope.$broadcast('zoomToFitChart');
        };

        let allNodes = [];
        let page = 1;

        let getNodes = function () {
            // Get the workflow nodes
            TemplatesService.getWorkflowJobTemplateNodes($scope.workflowJobTemplateObj.id, page)
                .then(function (data) {
                    for (var i = 0; i < data.data.results.length; i++) {
                        allNodes.push(data.data.results[i]);
                    }
                    if (data.data.next) {
                        // Get the next page
                        page++;
                        getNodes();
                    } else {
                        let arrayOfLinksForChart = [];
                        let arrayOfNodesForChart = [];

                        ({arrayOfNodesForChart, arrayOfLinksForChart, chartNodeIdToIndexMapping, nodeIdToChartNodeIdMapping, nodeRef, workflowMakerNodeIdCounter} = WorkflowChartService.generateArraysOfNodesAndLinks(allNodes));

                        let depthMap = WorkflowChartService.generateDepthMap(arrayOfLinksForChart);

                        $scope.graphState = { arrayOfNodesForChart, arrayOfLinksForChart, depthMap };
                    }
                }, function ({ data, status, config }) {
                    ProcessErrors($scope, data, status, null, {
                        hdr: $scope.strings.get('error.HEADER'),
                        msg: $scope.strings.get('error.CALL', {
                            path: `${config.url}`,
                            action: `${config.method}`,
                            status
                        })
                    });
                });
        };

        getNodes();
    }
];
