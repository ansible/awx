/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'WorkflowService', 'TemplatesService',
    'ProcessErrors', 'CreateSelect2', '$q', 'JobTemplateModel',
    'Empty', 'PromptService', 'Rest', 'TemplatesStrings', '$timeout',
    function ($scope, WorkflowService, TemplatesService,
        ProcessErrors, CreateSelect2, $q, JobTemplate,
        Empty, PromptService, Rest, TemplatesStrings, $timeout) {

        $scope.strings = TemplatesStrings;
        // TODO: I don't think this needs to be on scope but changing it will require changes to
        // all the prompt places
        $scope.preventCredsWithPasswords = true;

        let editRequests = [];
        let associateRequests = [];
        let disassociateRequests = [];
        let credentialRequests = [];

        $scope.showKey = false;
        $scope.toggleKey = () => $scope.showKey = !$scope.showKey;
        $scope.keyClassList = `{ 'Key-menuIcon--active': showKey }`;

        $scope.formState = {
            'showNodeForm': false,
            'showLinkForm': false
        };

        function recursiveNodeUpdates(params, completionCallback) {
            // params.parentId
            // params.node

            let buildSendableNodeData = function () {
                // Create the node
                let sendableNodeData = {
                    unified_job_template: params.node.unifiedJobTemplate.id,
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

                if (_.has(params, 'node.promptData.extraVars')) {
                    if (_.get(params, 'node.promptData.launchConf.defaults.extra_vars')) {
                        const defaultVars = jsyaml.safeLoad(params.node.promptData.launchConf.defaults.extra_vars);

                        // Only include extra vars that differ from the template default vars
                        _.forOwn(params.node.promptData.extraVars, (value, key) => {
                            if (!defaultVars[key] || defaultVars[key] !== value) {
                                sendableNodeData.extra_data[key] = value;
                            }
                        });
                        if (_.isEmpty(sendableNodeData.extra_data)) {
                            delete sendableNodeData.extra_data;
                        }
                    } else {
                        if (_.has(params, 'node.promptData.extraVars') && !_.isEmpty(params.node.promptData.extraVars)) {
                            sendableNodeData.extra_data = params.node.promptData.extraVars;
                        }
                    }
                }

                // Check to see if the user has provided any prompt values that are different
                // from the defaults in the job template

                if (params.node.unifiedJobTemplate.type === "job_template" && params.node.promptData) {
                    sendableNodeData = PromptService.bundlePromptDataForSaving({
                        promptData: params.node.promptData,
                        dataToSave: sendableNodeData
                    });
                }

                return sendableNodeData;
            };

            let continueRecursing = function (parentId) {
                $scope.totalIteratedNodes++;

                if ($scope.totalIteratedNodes === $scope.treeData.data.totalNodes) {
                    // We're done recursing, lets move on
                    completionCallback();
                } else {
                    if (params.node.children && params.node.children.length > 0) {
                        _.forEach(params.node.children, function (child) {
                            if (child.edgeType === "success") {
                                recursiveNodeUpdates({
                                    parentId: parentId,
                                    node: child
                                }, completionCallback);
                            } else if (child.edgeType === "failure") {
                                recursiveNodeUpdates({
                                    parentId: parentId,
                                    node: child
                                }, completionCallback);
                            } else if (child.edgeType === "always") {
                                recursiveNodeUpdates({
                                    parentId: parentId,
                                    node: child
                                }, completionCallback);
                            }
                        });
                    }
                }
            };

            if (params.node.isNew) {

                TemplatesService.addWorkflowNode({
                        url: $scope.treeData.workflow_job_template_obj.related.workflow_nodes,
                        data: buildSendableNodeData()
                    })
                    .then(function (data) {

                        if (!params.node.isRoot) {
                            associateRequests.push({
                                parentId: params.parentId,
                                nodeId: data.data.id,
                                edge: params.node.edgeType
                            });
                        }

                        if (_.get(params, 'node.promptData.launchConf.ask_credential_on_launch')) {
                            // This finds the credentials that were selected in the prompt but don't occur
                            // in the template defaults
                            let credentialsToPost = params.node.promptData.prompts.credentials.value.filter(function (credFromPrompt) {
                                let defaultCreds = _.get(params, 'node.promptData.launchConf.defaults.credentials', []);
                                return !defaultCreds.some(function (defaultCred) {
                                    return credFromPrompt.id === defaultCred.id;
                                });
                            });

                            credentialsToPost.forEach((credentialToPost) => {
                                credentialRequests.push({
                                    id: data.data.id,
                                    data: {
                                        id: credentialToPost.id
                                    }
                                });
                            });
                        }

                        params.node.isNew = false;
                        continueRecursing(data.data.id);
                    }, function ({ data, config, status }) {
                        ProcessErrors($scope, data, status, null, {
                            hdr: $scope.strings.get('error.HEADER'),
                            msg: $scope.strings.get('error.CALL', {
                                path: `${config.url}`,
                                action: `${config.method}`,
                                status
                            })
                        });
                    });
            } else {
                if (params.node.edited || !params.node.originalParentId || (params.node.originalParentId && (params.parentId !== params.node.originalParentId  || params.node.originalEdge !== params.node.edgeType))) {

                    if (params.node.edited) {

                        editRequests.push({
                            id: params.node.nodeId,
                            data: buildSendableNodeData()
                        });

                        if (_.get(params, 'node.promptData.launchConf.ask_credential_on_launch')) {
                            let credentialsNotInPriorCredentials = params.node.promptData.prompts.credentials.value.filter(function (credFromPrompt) {
                                let defaultCreds = _.get(params, 'node.promptData.launchConf.defaults.credentials', []);
                                return !defaultCreds.some(function (defaultCred) {
                                    return credFromPrompt.id === defaultCred.id;
                                });
                            });

                            let credentialsToAdd = credentialsNotInPriorCredentials.filter(function (credNotInPrior) {
                                let previousOverrides = _.get(params, 'node.promptData.prompts.credentials.previousOverrides', []);
                                return !previousOverrides.some(function (priorCred) {
                                    return credNotInPrior.id === priorCred.id;
                                });
                            });

                            let credentialsToRemove = [];

                            if (_.has(params, 'node.promptData.prompts.credentials.previousOverrides')) {
                                credentialsToRemove = params.node.promptData.prompts.credentials.previousOverrides.filter(function (priorCred) {
                                    return !credentialsNotInPriorCredentials.some(function (credNotInPrior) {
                                        return priorCred.id === credNotInPrior.id;
                                    });
                                });
                            }

                            credentialsToAdd.forEach((credentialToAdd) => {
                                credentialRequests.push({
                                    id: params.node.nodeId,
                                    data: {
                                        id: credentialToAdd.id
                                    }
                                });
                            });

                            credentialsToRemove.forEach((credentialToRemove) => {
                                credentialRequests.push({
                                    id: params.node.nodeId,
                                    data: {
                                        id: credentialToRemove.id,
                                        disassociate: true
                                    }
                                });
                            });
                        }
                    }

                    if (params.node.originalParentId && (params.parentId !== params.node.originalParentId || params.node.originalEdge !== params.node.edgeType)) {
                        let parentIsDeleted = false;

                        _.forEach($scope.treeData.data.deletedNodes, function (deletedNode) {
                            if (deletedNode === params.node.originalParentId) {
                                parentIsDeleted = true;
                            }
                        });

                        if (!parentIsDeleted) {
                            disassociateRequests.push({
                                parentId: params.node.originalParentId,
                                nodeId: params.node.nodeId,
                                edge: params.node.originalEdge
                            });
                        }

                        // Can only associate if we have a parent.
                        // If we don't have a parent then this is a root node
                        // and the act of disassociating will make it a root node
                        if (params.parentId) {
                            associateRequests.push({
                                parentId: params.parentId,
                                nodeId: params.node.nodeId,
                                edge: params.node.edgeType
                            });
                        }

                    } else if (!params.node.originalParentId && params.parentId) {
                        // This used to be a root node but is now not a root node
                        associateRequests.push({
                            parentId: params.parentId,
                            nodeId: params.node.nodeId,
                            edge: params.node.edgeType
                        });
                    }

                }

                continueRecursing(params.node.nodeId);
            }
        }

        $scope.closeWorkflowMaker = function() {
            // Revert the data to the master which was created when the dialog was opened
            $scope.treeData.data = angular.copy($scope.treeDataMaster);
            $scope.closeDialog();
        };

        $scope.saveWorkflowMaker = function () {

            $scope.totalIteratedNodes = 0;

            if ($scope.treeData && $scope.treeData.data && $scope.treeData.data.children && $scope.treeData.data.children.length > 0) {
                let completionCallback = function () {

                    let disassociatePromises = disassociateRequests.map(function (request) {
                        return TemplatesService.disassociateWorkflowNode({
                            parentId: request.parentId,
                            nodeId: request.nodeId,
                            edge: request.edge
                        });
                    });

                    let editNodePromises = editRequests.map(function (request) {
                        return TemplatesService.editWorkflowNode({
                            id: request.id,
                            data: request.data
                        });
                    });

                    let deletePromises = $scope.treeData.data.deletedNodes.map(function (nodeId) {
                        return TemplatesService.deleteWorkflowJobTemplateNode(nodeId);
                    });

                    $q.all(disassociatePromises.concat(editNodePromises, deletePromises))
                        .then(function () {

                            let credentialPromises = credentialRequests.map(function (request) {
                                return TemplatesService.postWorkflowNodeCredential({
                                    id: request.id,
                                    data: request.data
                                });
                            });

                            let associatePromises = associateRequests.map(function (request) {
                                return TemplatesService.associateWorkflowNode({
                                    parentId: request.parentId,
                                    nodeId: request.nodeId,
                                    edge: request.edge
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
                };

                _.forEach($scope.treeData.data.children, function (child) {
                    recursiveNodeUpdates({
                        node: child
                    }, completionCallback);
                });
            } else {

                let deletePromises = $scope.treeData.data.deletedNodes.map(function (nodeId) {
                    return TemplatesService.deleteWorkflowJobTemplateNode(nodeId);
                });

                $q.all(deletePromises)
                    .then(function () {
                        $scope.closeDialog();
                    });
            }
        };

        /* ADD NODE FUNCTIONS */

        $scope.startAddNode = function (parent, betweenTwoNodes) {

            if ($scope.nodeBeingWorkedOn) {
                $scope.cancelNodeForm();
            }

            if ($scope.linkBeingWorkedOn) {
                $scope.cancelLinkForm();
            }

            $scope.nodeBeingWorkedOn = WorkflowService.addPlaceholderNode({
                parent: parent,
                betweenTwoNodes: betweenTwoNodes,
                tree: $scope.treeData.data,
                id: $scope.treeData.nextIndex
            });

            $scope.treeData.nextIndex++;

            $scope.$broadcast("refreshWorkflowChart");

            $scope.nodeFormMode = "add";
            $scope.formState.showNodeForm = true;
        };

        $scope.confirmNodeForm = function(selectedTemplate, promptData, edgeType) {
            if ($scope.nodeFormMode === "add") {
                if (selectedTemplate && edgeType && edgeType.value) {
                    $scope.nodeBeingWorkedOn.unifiedJobTemplate = selectedTemplate;
                    $scope.nodeBeingWorkedOn.edgeType = edgeType.value;
                    if ($scope.nodeBeingWorkedOn.unifiedJobTemplate.type === 'job_template') {
                        $scope.nodeBeingWorkedOn.promptData = _.cloneDeep(promptData);
                    }
                    $scope.nodeBeingWorkedOn.canEdit = true;

                    delete $scope.nodeBeingWorkedOn.placeholder;

                    // Increment the total node counter
                    $scope.treeData.data.totalNodes++;

                }
            } else if ($scope.nodeFormMode === "edit") {
                if (selectedTemplate) {
                    $scope.nodeBeingWorkedOn.unifiedJobTemplate = selectedTemplate;

                    if ($scope.nodeBeingWorkedOn.unifiedJobTemplate.type === 'job_template') {
                        $scope.nodeBeingWorkedOn.promptData = _.cloneDeep(promptData);
                    }

                    $scope.nodeBeingWorkedOn.isActiveEdit = false;

                    $scope.nodeBeingWorkedOn.edited = true;
                }
            }

            $scope.formState.showNodeForm = false;
            $scope.nodeFormMode = null;
            $scope.nodeBeingWorkedOn = null;

            $scope.$broadcast("refreshWorkflowChart");
        };

        $scope.cancelNodeForm = function() {
            if ($scope.nodeFormMode === "add") {
                // Remove the placeholder node from the tree
                WorkflowService.removeNodeFromTree({
                    tree: $scope.treeData.data,
                    nodeToBeDeleted: $scope.nodeBeingWorkedOn
                });
            } else if ($scope.nodeFormMode === "edit") {
                $scope.nodeBeingWorkedOn.isActiveEdit = false;
            }
            $scope.formState.showNodeForm = false;
            $scope.nodeBeingWorkedOn = null;
            $scope.nodeFormMode = null;
            $scope.$broadcast("refreshWorkflowChart");
        };

        /* EDIT NODE FUNCTIONS */

        $scope.startEditNode = function(nodeToEdit) {
            if ($scope.linkBeingWorkedOn) {
                $scope.cancelLinkForm();
            }

            if (!$scope.nodeBeingWorkedOn || ($scope.nodeBeingWorkedOn && $scope.nodeBeingWorkedOn.id !== nodeToEdit.id)) {
                if ($scope.nodeBeingWorkedOn) {
                    $scope.cancelNodeForm();
                }

                $scope.nodeFormMode = "edit";

                $scope.formState.showNodeForm = true;

                let parent = WorkflowService.searchTree({
                    element: $scope.treeData.data,
                    matchingId: nodeToEdit.parent.id
                });

                $scope.nodeBeingWorkedOn = WorkflowService.searchTree({
                    element: parent,
                    matchingId: nodeToEdit.id
                });

                $scope.nodeBeingWorkedOn.isActiveEdit = true;
            }

            $scope.$broadcast("refreshWorkflowChart");
        }

        /* EDIT LINK FUNCTIONS */

        $scope.startEditLink = (parentId, childId) => {
            const setupLinkEdit = () => {
                const parentNode = WorkflowService.searchTree({
                    element: $scope.treeData.data,
                    matchingId: parentId
                });

                parentNode.isLinkEditParent = true;

                // Loop across children looking for childId
                const childNode = _.find(parentNode.children, {'id': childId});

                childNode.isLinkEditChild = true;

                $scope.linkBeingWorkedOn = {
                    parent: parentNode,
                    child: childNode
                }

                $scope.linkConfig = {
                    parent: {
                        id: parentId,
                        name: parentNode.unifiedJobTemplate.name
                    },
                    child: {
                        id: childId,
                        name: childNode.unifiedJobTemplate.name
                    },
                    edgeType: childNode.edgeType
                }
                $scope.formState.showLinkForm = true;

                $scope.$broadcast("refreshWorkflowChart");
            }

            if ($scope.nodeBeingWorkedOn) {
                $scope.cancelNodeForm();
            }

            if ($scope.linkBeingWorkedOn) {
                if ($scope.linkBeingWorkedOn.parent.nodeId !== parentId || $scope.linkBeingWorkedOn.child.nodeId !== childId) {
                    $scope.linkBeingWorkedOn.parent.isLinkEditParent = false;
                    $scope.linkBeingWorkedOn.child.isLinkEditChild = false;
                    setupLinkEdit()
                }
            } else {
                setupLinkEdit();
            }

        };

        $scope.confirmLinkForm = (newEdgeType) => {
            $scope.linkBeingWorkedOn.parent.isLinkEditParent = false;
            $scope.linkBeingWorkedOn.child.isLinkEditChild = false;
            $scope.linkBeingWorkedOn.child.edgeType = newEdgeType;
            $scope.linkBeingWorkedOn = null;
            $scope.formState.showLinkForm = false;
            $scope.$broadcast("refreshWorkflowChart");
        }

        $scope.cancelLinkForm = () => {
            $scope.linkBeingWorkedOn.parent.isLinkEditParent = false;
            $scope.linkBeingWorkedOn.child.isLinkEditChild = false;
            $scope.linkBeingWorkedOn = null;
            $scope.formState.showLinkForm = false;
            $scope.$broadcast("refreshWorkflowChart");
        };

        /* DELETE NODE FUNCTIONS */

        function resetDeleteNode() {
            $scope.nodeToBeDeleted = null;
            $scope.deleteOverlayVisible = false;
        }

        $scope.startDeleteNode = function (nodeToDelete) {
            $scope.nodeToBeDeleted = nodeToDelete;
            $scope.deleteOverlayVisible = true;
        };

        $scope.cancelDeleteNode = function () {
            resetDeleteNode();
        };

        $scope.confirmDeleteNode = function () {
            if ($scope.nodeToBeDeleted) {

                if ($scope.linkBeingWorkedOn) {
                    $scope.cancelLinkForm();
                }

                // TODO: turn this into a promise so that we can handle errors

                WorkflowService.removeNodeFromTree({
                    tree: $scope.treeData.data,
                    nodeToBeDeleted: $scope.nodeToBeDeleted
                });

                if ($scope.nodeToBeDeleted.isNew !== true) {
                    $scope.treeData.data.deletedNodes.push($scope.nodeToBeDeleted.nodeId);
                }

                resetDeleteNode();

                $scope.$broadcast("refreshWorkflowChart");

                $scope.treeData.data.totalNodes--;
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

        let buildTreeFromNodes = function () {
            WorkflowService.buildTree({
                workflowNodes: allNodes
            }).then(function (data) {
                $scope.treeData = data;

                // TODO: I think that the workflow chart directive (and eventually d3) is meddling with
                // this treeData object and removing the children object for some reason (?)
                // This happens on occasion and I think is a race condition (?)
                if (!$scope.treeData.data.children) {
                    $scope.treeData.data.children = [];
                }

                $scope.treeData.workflow_job_template_obj = $scope.workflowJobTemplateObj;

                $scope.treeDataMaster = angular.copy($scope.treeData.data);
                $scope.showManualControls = false;
            });
        };

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
                        // This is the last page
                        buildTreeFromNodes();
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
