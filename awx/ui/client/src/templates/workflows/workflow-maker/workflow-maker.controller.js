/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'TemplatesService',
    'ProcessErrors', 'CreateSelect2', '$q', 'JobTemplateModel',
    'Empty', 'PromptService', 'Rest', 'TemplatesStrings',
    function ($scope, TemplatesService,
        ProcessErrors, CreateSelect2, $q, JobTemplate,
        Empty, PromptService, Rest, TemplatesStrings) {

        $scope.strings = TemplatesStrings;
        // TODO: I don't think this needs to be on scope but changing it will require changes to
        // all the prompt places
        $scope.preventCredsWithPasswords = true;

        let credentialRequests = [];
        let deletedNodeIds = [];
        let workflowMakerNodeIdCounter = 1;
        let nodeIdToMakerIdMapping = {};
        let chartNodeIdToIndexMapping = {};
        let nodeRef = {};

        // TODO: fix this
        $scope.totalNodes = 0;

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
            $scope.treeState.nodeTree = angular.copy($scope.treeStateMaster);
            $scope.closeDialog();
        };

        $scope.saveWorkflowMaker = function () {

            if ($scope.treeState.arrayOfNodesForChart.length > 1) {
                let addPromises = [];
                let editPromises = [];

                Object.keys(nodeRef).map((workflowMakerNodeId) => {
                    if (nodeRef[workflowMakerNodeId].isNew) {
                        addPromises.push(TemplatesService.addWorkflowNode({
                            url: $scope.workflowJobTemplateObj.related.workflow_nodes,
                            data: buildSendableNodeData(nodeRef[workflowMakerNodeId])
                        }).then(({data}) => {
                            nodeRef[workflowMakerNodeId].originalNodeObject = data;
                            // TODO: do we need this?
                            nodeIdToMakerIdMapping[data.id] = parseInt(workflowMakerNodeId);
                            // if (_.get(params, 'node.promptData.launchConf.ask_credential_on_launch')) {
                            //     // This finds the credentials that were selected in the prompt but don't occur
                            //     // in the template defaults
                            //     let credentialsToPost = params.node.promptData.prompts.credentials.value.filter(function (credFromPrompt) {
                            //         let defaultCreds = _.get(params, 'node.promptData.launchConf.defaults.credentials', []);
                            //         return !defaultCreds.some(function (defaultCred) {
                            //             return credFromPrompt.id === defaultCred.id;
                            //         });
                            //     });
                            //
                            //     credentialsToPost.forEach((credentialToPost) => {
                            //         credentialRequests.push({
                            //             id: data.data.id,
                            //             data: {
                            //                 id: credentialToPost.id
                            //             }
                            //         });
                            //     });
                            // }
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
                        $scope.treeState.arrayOfLinksForChart.forEach(link => {
                            // link.source.index of 0 is our artificial start node
                            if (link.source.index !== 0) {
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
                                const foo = nodeIdToMakerIdMapping[sourceNodeId];
                                const bar = nodeIdToMakerIdMapping[targetNodeId];
                                switch(linkMap[sourceNodeId][targetNodeId]) {
                                    case "success":
                                        if (
                                            !nodeRef[foo].originalNodeObject.success_nodes ||
                                            !nodeRef[foo].originalNodeObject.success_nodes.includes(nodeRef[bar].id)
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
                                            !nodeRef[foo].originalNodeObject.failure_nodes ||
                                            !nodeRef[foo].originalNodeObject.failure_nodes.includes(nodeRef[bar].id)
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
                                            !nodeRef[foo].originalNodeObject.always_nodes ||
                                            !nodeRef[foo].originalNodeObject.always_nodes.includes(nodeRef[bar].id)
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

                                // TODO: don't forget about this....
                                let credentialPromises = credentialRequests.map(function (request) {
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

            // TODO: handle the case where the user deletes all the nodes

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

            $scope.treeState.arrayOfNodesForChart.push({
                index: $scope.treeState.arrayOfNodesForChart.length,
                id: workflowMakerNodeIdCounter,
                isNodeBeingAdded: true,
                unifiedJobTemplate: null
            });

            chartNodeIdToIndexMapping[workflowMakerNodeIdCounter] = $scope.treeState.arrayOfNodesForChart.length - 1;

            $scope.treeState.arrayOfLinksForChart.push({
                source: $scope.treeState.arrayOfNodesForChart[parent.index],
                target: $scope.treeState.arrayOfNodesForChart[chartNodeIdToIndexMapping[workflowMakerNodeIdCounter]],
                edgeType: "placeholder"
            });

            $scope.nodeConfig = {
                mode: "add",
                nodeId: workflowMakerNodeIdCounter,
                newNodeIsRoot: parent.index === 0
            };

            workflowMakerNodeIdCounter++;

            $scope.$broadcast("refreshWorkflowChart");

            $scope.formState.showNodeForm = true;
        };

        $scope.startAddNodeWithChild = function (link) {
            if ($scope.nodeConfig) {
                $scope.cancelNodeForm();
            }

            $scope.treeState.arrayOfNodesForChart.push({
                index: $scope.treeState.arrayOfNodesForChart.length,
                id: workflowMakerNodeIdCounter,
                isNodeBeingAdded: true,
                unifiedJobTemplate: null
            });

            chartNodeIdToIndexMapping[workflowMakerNodeIdCounter] = $scope.treeState.arrayOfNodesForChart.length - 1;

            $scope.treeState.arrayOfLinksForChart.push({
                source: $scope.treeState.arrayOfNodesForChart[link.source.index],
                target: $scope.treeState.arrayOfNodesForChart[chartNodeIdToIndexMapping[workflowMakerNodeIdCounter]],
                edgeType: "placeholder"
            });

            $scope.nodeConfig = {
                mode: "add",
                nodeId: workflowMakerNodeIdCounter,
                newNodeIsRoot: link.source.index === 0
            };

            // Search for the link that used to exist between source and target and shift it to
            // go from our new node to the target
            $scope.treeState.arrayOfLinksForChart.forEach((foo) => {
                if (foo.source.id === link.source.id && foo.target.id === link.target.id) {
                    foo.source = $scope.treeState.arrayOfNodesForChart[chartNodeIdToIndexMapping[workflowMakerNodeIdCounter]];
                }
            });

            workflowMakerNodeIdCounter++;

            $scope.$broadcast("refreshWorkflowChart");

            $scope.formState.showNodeForm = true;
        };

        $scope.confirmNodeForm = function(selectedTemplate, promptData, edgeType) {
            const nodeIndex = chartNodeIdToIndexMapping[$scope.nodeConfig.nodeId];
            if ($scope.nodeConfig.mode === "add") {
                if (selectedTemplate && edgeType && edgeType.value) {
                    // TODO: do we need to clone prompt data?
                    nodeRef[$scope.nodeConfig.nodeId] = {
                        fullUnifiedJobTemplateObject: selectedTemplate,
                        promptData: _.cloneDeep(promptData),
                        isNew: true
                    };

                    $scope.treeState.arrayOfNodesForChart[nodeIndex].unifiedJobTemplate = selectedTemplate;
                    $scope.treeState.arrayOfNodesForChart[nodeIndex].isNodeBeingAdded = false;

                    $scope.treeState.arrayOfLinksForChart.map( (link) => {
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
                    $scope.treeState.arrayOfNodesForChart[nodeIndex].unifiedJobTemplate = selectedTemplate;
                    $scope.treeState.arrayOfNodesForChart[nodeIndex].isNodeBeingEdited = false;
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
                $scope.treeState.arrayOfNodesForChart.splice(nodeIndex, 1);

                // Update the links
                let parents = [];
                let children = [];

                // Remove any links that reference this node
                for( let i = $scope.treeState.arrayOfLinksForChart.length; i--; ){
                    const link = $scope.treeState.arrayOfLinksForChart[i];

                    if (link.source.index === nodeIndex || link.target.index === nodeIndex) {
                        if (link.source.index === nodeIndex) {
                            const targetIndex = link.target.index < nodeIndex ? link.target.index : link.target.index - 1;
                            children.push({index: targetIndex, edgeType: link.edgeType});
                        } else if (link.target.index === nodeIndex) {
                            const sourceIndex = link.source.index < nodeIndex ? link.source.index : link.source.index - 1;
                            parents.push(sourceIndex);
                        }
                        $scope.treeState.arrayOfLinksForChart.splice(i, 1);
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
                        $scope.treeState.arrayOfLinksForChart.push({
                            source: $scope.treeState.arrayOfNodesForChart[parentIndex],
                            target: $scope.treeState.arrayOfNodesForChart[child.index],
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
            } else if ($scope.nodeConfig.mode === "edit") {
                $scope.treeState.arrayOfNodesForChart.map( (node) => {
                    if (node.index === $scope.nodeConfig.nodeId) {
                        node.isNodeBeingEdited = false;
                    }
                });
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

                $scope.treeState.arrayOfNodesForChart.map( (node) => {
                    if (node.index === nodeToEdit.index) {
                        node.isNodeBeingEdited = true;
                    }
                });

                $scope.formState.showNodeForm = true;
            }

            $scope.$broadcast("refreshWorkflowChart");
        };

        /* LINK FUNCTIONS */

        $scope.startEditLink = (linkToEdit) => {
            const setupLinkEdit = () => {

                linkToEdit.isLinkBeingEdited = true;

                // Determine whether or not this link can be removed
                // TODO: we already (potentially) loop across this array below
                // and we should combine
                let numberOfParents = 0;
                $scope.treeState.arrayOfLinksForChart.forEach((link) => {
                    if (link.target.id === linkToEdit.target.id) {
                        numberOfParents++;
                    }
                });

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
                        $scope.treeState.arrayOfLinksForChart.splice($scope.treeState.arrayOfLinksForChart.length-1, 1);
                    }
                    $scope.treeState.arrayOfLinksForChart.forEach((link) => {
                        link.isLinkBeingEdited = false;
                    });
                    setupLinkEdit();
                }
            } else {
                setupLinkEdit();
            }

        };

        $scope.selectNodeForLinking = (node) => {
            // start here
            if ($scope.linkConfig) {
                // This is the second node selected
                $scope.linkConfig.child = {
                    id: node.id,
                    name: node.unifiedJobTemplate.name
                };
                $scope.linkConfig.edgeType = "success";

                $scope.treeState.arrayOfNodesForChart.forEach((node) => {
                    node.isInvalidLinkTarget = false;
                });

                $scope.treeState.arrayOfLinksForChart.push({
                    target: $scope.treeState.arrayOfNodesForChart[node.index],
                    source: $scope.treeState.arrayOfNodesForChart[chartNodeIdToIndexMapping[$scope.linkConfig.parent.id]],
                    edgeType: "placeholder",
                    isLinkBeingEdited: true
                });

                $scope.treeState.isLinkMode = false;
            } else {
                // This is the first node selected
                $scope.treeState.addLinkSource = node.id;
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
                $scope.treeState.arrayOfLinksForChart.forEach((link) => {
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
                    $scope.treeState.arrayOfNodesForChart[chartNodeIdToIndexMapping[ancestorId]].isInvalidLinkTarget = true;
                });

                $scope.treeState.isLinkMode = true;

                $scope.formState.showLinkForm = true;
            }

            $scope.$broadcast("refreshWorkflowChart");
        };

        $scope.confirmLinkForm = (newEdgeType) => {
            $scope.treeState.arrayOfLinksForChart.forEach((link) => {
                if (link.source.id === $scope.linkConfig.parent.id && link.target.id === $scope.linkConfig.child.id) {
                    link.source.isLinkEditParent = false;
                    link.target.isLinkEditChild = false;
                    link.edgeType = newEdgeType;
                    link.isLinkBeingEdited = false;
                }
            });

            if ($scope.linkConfig.mode === "add") {
                $scope.treeState.arrayOfNodesForChart.forEach((node) => {
                    node.isInvalidLinkTarget = false;
                });
            }

            $scope.treeState.addLinkSource = null;
            $scope.formState.showLinkForm = false;
            $scope.linkConfig = null;
            $scope.$broadcast("refreshWorkflowChart");
        };

        $scope.unlink = () => {
            // Remove the link
            for( let i = $scope.treeState.arrayOfLinksForChart.length; i--; ){
                const link = $scope.treeState.arrayOfLinksForChart[i];

                if (link.source.id === $scope.linkConfig.parent.id && link.target.id === $scope.linkConfig.child.id) {
                    $scope.treeState.arrayOfLinksForChart.splice(i, 1);
                }
            }

            $scope.formState.showLinkForm = false;
            $scope.linkConfig = null;
            $scope.$broadcast("refreshWorkflowChart");
        };

        $scope.cancelLinkForm = () => {
            if ($scope.linkConfig.mode === "add" && $scope.linkConfig.child) {
                $scope.treeState.arrayOfLinksForChart.splice($scope.treeState.arrayOfLinksForChart.length-1, 1);
            }
            $scope.treeState.addLinkSource = null;
            $scope.treeState.isLinkMode = false;
            $scope.formState.showLinkForm = false;
            $scope.treeState.arrayOfNodesForChart.forEach((node) => {
                node.isInvalidLinkTarget = false;
            });
            $scope.treeState.arrayOfLinksForChart.forEach((link) => {
                link.isLinkBeingEdited = false;
            });
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
                $scope.treeState.arrayOfNodesForChart.splice(nodeIndex, 1);

                // Update the links
                let parents = [];
                let children = [];

                // Remove any links that reference this node
                for( let i = $scope.treeState.arrayOfLinksForChart.length; i--; ){
                    const link = $scope.treeState.arrayOfLinksForChart[i];

                    if (link.source.index === nodeIndex || link.target.index === nodeIndex) {
                        if (link.source.index === nodeIndex) {
                            const targetIndex = link.target.index < nodeIndex ? link.target.index : link.target.index - 1;
                            children.push({index: targetIndex, edgeType: link.edgeType});
                        } else if (link.target.index === nodeIndex) {
                            const sourceIndex = link.source.index < nodeIndex ? link.source.index : link.source.index - 1;
                            parents.push(sourceIndex);
                        }
                        $scope.treeState.arrayOfLinksForChart.splice(i, 1);
                    } else {
                        if (link.source.index > nodeIndex) {
                            link.source = link.source.index - 1;
                        }
                        if (link.target.index > nodeIndex) {
                            link.target = link.target.index - 1;
                        }
                    }
                }

                // Add the new links
                parents.forEach((parentIndex) => {
                    children.forEach((child) => {
                        if (parentIndex === 0) {
                            child.edgeType = "always";
                        }
                        $scope.treeState.arrayOfLinksForChart.push({
                            source: $scope.treeState.arrayOfNodesForChart[parentIndex],
                            target: $scope.treeState.arrayOfNodesForChart[child.index],
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
                        allNodes.forEach((node) => {
                            node.workflowMakerNodeId = workflowMakerNodeIdCounter;
                            nodeRef[workflowMakerNodeIdCounter] = {
                                originalNodeObject: node
                            };
                            arrayOfNodesForChart.push({
                                index: workflowMakerNodeIdCounter-1,
                                id: workflowMakerNodeIdCounter,
                                unifiedJobTemplate: node.summary_fields.unified_job_template
                            });
                            allNodeIds.push(node.id);
                            nodeIdToMakerIdMapping[node.id] = node.workflowMakerNodeId;
                            chartNodeIdToIndexMapping[workflowMakerNodeIdCounter] = workflowMakerNodeIdCounter-1;
                            workflowMakerNodeIdCounter++;
                        });

                        allNodes.forEach((node) => {
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
