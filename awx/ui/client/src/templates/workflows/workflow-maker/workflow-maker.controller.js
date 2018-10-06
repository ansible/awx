/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'WorkflowService', 'TemplatesService',
    'ProcessErrors', 'CreateSelect2', '$q', 'JobTemplateModel', 'WorkflowJobTemplateModel',
    'Empty', 'PromptService', 'Rest', 'TemplatesStrings', '$timeout',
    function ($scope, WorkflowService, TemplatesService,
        ProcessErrors, CreateSelect2, $q, JobTemplate, WorkflowJobTemplate,
        Empty, PromptService, Rest, TemplatesStrings, $timeout) {

        let promptWatcher, surveyQuestionWatcher, credentialsWatcher;

        $scope.strings = TemplatesStrings;
        $scope.preventCredsWithPasswords = true;

        $scope.workflowMakerFormConfig = {
            nodeMode: "idle",
            activeTab: "jobs",
            formIsValid: false
        };

        $scope.job_type_options = [{
            label: $scope.strings.get('workflow_maker.RUN'),
            value: "run"
        }, {
            label: $scope.strings.get('workflow_maker.CHECK'),
            value: "check"
        }];

        $scope.edgeTypeOptions = createEdgeTypeOptions();

        let editRequests = [];
        let associateRequests = [];
        let disassociateRequests = [];
        let credentialRequests = [];

        $scope.showKey = false;
        $scope.toggleKey = () => $scope.showKey = !$scope.showKey;
        $scope.keyClassList = `{ 'Key-menuIcon--active': showKey }`;

        function createEdgeTypeOptions() {
            return ([{
                    label: $scope.strings.get('workflow_maker.ALWAYS'),
                    value: 'always'
                },
                {
                    label: $scope.strings.get('workflow_maker.ON_SUCCESS'),
                    value: 'success'
                },
                {
                    label: $scope.strings.get('workflow_maker.ON_FAILURE'),
                    value: 'failure'
                }
            ]);
        }

        function resetNodeForm() {
            $scope.workflowMakerFormConfig.nodeMode = "idle";
            delete $scope.selectedTemplate;
            delete $scope.placeholderNode;
            delete $scope.betweenTwoNodes;
            $scope.nodeBeingEdited = null;
            $scope.workflowMakerFormConfig.activeTab = "jobs";

            $scope.$broadcast('clearWorkflowLists');
        }

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

                if ((params.node.unifiedJobTemplate.type === "job_template" || params.node.unifiedJobTemplate.type === "workflow_job_template") && params.node.promptData) {
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
                    }, function ({
                        data,
                        config,
                        status
                    }) {
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
                if (params.node.edited || !params.node.originalParentId || (params.node.originalParentId && params.parentId !== params.node.originalParentId)) {

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

        let updateEdgeDropdownOptions = (edgeTypeValue) => {
            // Not passing an edgeTypeValue will include all by default

            if (edgeTypeValue) {
                $scope.edgeTypeOptions = _.filter(createEdgeTypeOptions(), {
                    'value': edgeTypeValue
                });
            } else {
                $scope.edgeTypeOptions = createEdgeTypeOptions();
            }

            CreateSelect2({
                element: '#workflow_node_edge',
                multiple: false
            });
        };

        let checkCredentialsForRequiredPasswords = () => {
            let credentialRequiresPassword = false;
            $scope.promptData.prompts.credentials.value.forEach((credential) => {
                if ((credential.passwords_needed &&
                        credential.passwords_needed.length > 0) ||
                    (_.has(credential, 'inputs.vault_password') &&
                        credential.inputs.vault_password === "ASK")
                ) {
                    credentialRequiresPassword = true;
                }
            });
            $scope.credentialRequiresPassword = credentialRequiresPassword;
        };

        let watchForPromptChanges = () => {
            let promptDataToWatch = [
                'promptData.prompts.inventory.value',
                'promptData.prompts.verbosity.value',
                'missingSurveyValue'
            ];

            promptWatcher = $scope.$watchGroup(promptDataToWatch, function () {
                let missingPromptValue = false;
                if ($scope.missingSurveyValue) {
                    missingPromptValue = true;
                } else if ($scope.selectedTemplate.type === 'job_template' && (!$scope.promptData.prompts.inventory.value || !$scope.promptData.prompts.inventory.value.id)) {
                    missingPromptValue = true;
                }
                $scope.promptModalMissingReqFields = missingPromptValue;
            });

            if ($scope.promptData.launchConf.ask_credential_on_launch && $scope.credentialRequiresPassword) {
                credentialsWatcher = $scope.$watch('promptData.prompts.credentials', () => {
                    checkCredentialsForRequiredPasswords();
                });
            }
        };

        $scope.closeWorkflowMaker = function () {
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

            if ($scope.placeholderNode || $scope.nodeBeingEdited) {
                $scope.cancelNodeForm();
            }

            $scope.workflowMakerFormConfig.nodeMode = "add";
            $scope.addParent = parent;
            $scope.betweenTwoNodes = betweenTwoNodes;

            $scope.placeholderNode = WorkflowService.addPlaceholderNode({
                parent: parent,
                betweenTwoNodes: betweenTwoNodes,
                tree: $scope.treeData.data,
                id: $scope.treeData.nextIndex
            });

            $scope.treeData.nextIndex++;

            // Set the default to success
            let edgeType = {
                label: $scope.strings.get('workflow_maker.ON_SUCCESS'),
                value: "success"
            };

            if (parent && ((betweenTwoNodes && parent.source.isStartNode) || (!betweenTwoNodes && parent.isStartNode))) {
                // This node will always be executed
                updateEdgeDropdownOptions('always');
                edgeType = {
                    label: $scope.strings.get('workflow_maker.ALWAYS'),
                    value: "always"
                };
            } else {
                updateEdgeDropdownOptions();
            }

            $scope.edgeType = edgeType;
            $scope.$broadcast("refreshWorkflowChart");

        };

        $scope.confirmNodeForm = function () {
            if ($scope.workflowMakerFormConfig.nodeMode === "add") {
                if ($scope.selectedTemplate && $scope.edgeType && $scope.edgeType.value) {

                    $scope.placeholderNode.unifiedJobTemplate = $scope.selectedTemplate;
                    $scope.placeholderNode.edgeType = $scope.edgeType.value;
                    if ($scope.placeholderNode.unifiedJobTemplate.type === 'job_template' ||
                        $scope.placeholderNode.unifiedJobTemplate.type === 'workflow_job_template') {
                        $scope.placeholderNode.promptData = _.cloneDeep($scope.promptData);
                    }
                    $scope.placeholderNode.canEdit = true;

                    delete $scope.placeholderNode.placeholder;

                    resetNodeForm();

                    // Increment the total node counter
                    $scope.treeData.data.totalNodes++;

                }
            } else if ($scope.workflowMakerFormConfig.nodeMode === "edit") {
                if ($scope.selectedTemplate && $scope.edgeType && $scope.edgeType.value) {
                    $scope.nodeBeingEdited.unifiedJobTemplate = $scope.selectedTemplate;
                    $scope.nodeBeingEdited.edgeType = $scope.edgeType.value;
                    if ($scope.nodeBeingEdited.unifiedJobTemplate.type === 'job_template' || $scope.nodeBeingEdited.unifiedJobTemplate.type === 'workflow_job_template') {
                        $scope.nodeBeingEdited.promptData = _.cloneDeep($scope.promptData);
                    }

                    $scope.nodeBeingEdited.isActiveEdit = false;

                    $scope.nodeBeingEdited.edited = true;

                    resetNodeForm();
                }
            }

            if (promptWatcher) {
                promptWatcher();
            }

            if (surveyQuestionWatcher) {
                surveyQuestionWatcher();
            }

            if (credentialsWatcher) {
                credentialsWatcher();
            }

            $scope.promptData = null;

            $scope.$broadcast("refreshWorkflowChart");
        };

        $scope.cancelNodeForm = function () {
            if ($scope.workflowMakerFormConfig.nodeMode === "add") {
                // Remove the placeholder node from the tree
                WorkflowService.removeNodeFromTree({
                    tree: $scope.treeData.data,
                    nodeToBeDeleted: $scope.placeholderNode
                });
            } else if ($scope.workflowMakerFormConfig.nodeMode === "edit") {
                $scope.nodeBeingEdited.isActiveEdit = false;
            }

            if (promptWatcher) {
                promptWatcher();
            }

            if (surveyQuestionWatcher) {
                surveyQuestionWatcher();
            }

            if (credentialsWatcher) {
                credentialsWatcher();
            }

            $scope.promptData = null;
            $scope.selectedTemplateInvalid = false;
            $scope.showPromptButton = false;

            // Reset the form
            resetNodeForm();

            $scope.$broadcast("refreshWorkflowChart");
        };

        /* EDIT NODE FUNCTIONS */

        $scope.startEditNode = function (nodeToEdit) {

            if (!$scope.nodeBeingEdited || ($scope.nodeBeingEdited && $scope.nodeBeingEdited.id !== nodeToEdit.id)) {
                if ($scope.placeholderNode || $scope.nodeBeingEdited) {
                    $scope.cancelNodeForm();

                    // Refresh this object as the parent has changed
                    nodeToEdit = WorkflowService.searchTree({
                        element: $scope.treeData.data,
                        matchingId: nodeToEdit.id
                    });
                }

                $scope.workflowMakerFormConfig.nodeMode = "edit";

                let parent = WorkflowService.searchTree({
                    element: $scope.treeData.data,
                    matchingId: nodeToEdit.parent.id
                });

                $scope.nodeBeingEdited = WorkflowService.searchTree({
                    element: parent,
                    matchingId: nodeToEdit.id
                });

                $scope.nodeBeingEdited.isActiveEdit = true;

                let finishConfiguringEdit = function () {
                    let templateType = $scope.nodeBeingEdited.unifiedJobTemplate.type;
                    let jobTemplate = templateType === "workflow_job_template" ? new WorkflowJobTemplate() : new JobTemplate();
                    if (!_.isEmpty($scope.nodeBeingEdited.promptData)) {
                        $scope.promptData = _.cloneDeep($scope.nodeBeingEdited.promptData);
                        const launchConf = $scope.promptData.launchConf;

                        if (!launchConf.survey_enabled &&
                            !launchConf.ask_inventory_on_launch &&
                            !launchConf.ask_credential_on_launch &&
                            !launchConf.ask_verbosity_on_launch &&
                            !launchConf.ask_job_type_on_launch &&
                            !launchConf.ask_limit_on_launch &&
                            !launchConf.ask_tags_on_launch &&
                            !launchConf.ask_skip_tags_on_launch &&
                            !launchConf.ask_diff_mode_on_launch &&
                            !launchConf.credential_needed_to_start &&
                            !launchConf.ask_variables_on_launch &&
                            launchConf.variables_needed_to_start.length === 0) {
                            $scope.showPromptButton = false;
                            $scope.promptModalMissingReqFields = false;
                        } else {
                            $scope.showPromptButton = true;

                            if ($scope.nodeBeingEdited.unifiedJobTemplate.type === 'job_template' && launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory') && !_.has($scope, 'nodeBeingEdited.originalNodeObj.summary_fields.inventory')) {
                                $scope.promptModalMissingReqFields = true;
                            } else {
                                $scope.promptModalMissingReqFields = false;
                            }
                        }
                    } else if (
                        _.get($scope, 'nodeBeingEdited.unifiedJobTemplate.unified_job_type') === 'job' ||
                        _.get($scope, 'nodeBeingEdited.unifiedJobTemplate.type') === 'job_template' ||
                        _.get($scope, 'nodeBeingEdited.unifiedJobTemplate.unified_job_type') === 'workflow_job' ||
                        _.get($scope, 'nodeBeingEdited.unifiedJobTemplate.type') === 'workflow_job_template'
                    ) {
                        let promises = [jobTemplate.optionsLaunch($scope.nodeBeingEdited.unifiedJobTemplate.id), jobTemplate.getLaunch($scope.nodeBeingEdited.unifiedJobTemplate.id)];

                        if (_.has($scope, 'nodeBeingEdited.originalNodeObj.related.credentials')) {
                            Rest.setUrl($scope.nodeBeingEdited.originalNodeObj.related.credentials);
                            promises.push(Rest.get());
                        }

                        $q.all(promises)
                            .then((responses) => {
                                let launchOptions = responses[0].data,
                                    launchConf = responses[1].data,
                                    workflowNodeCredentials = responses[2] ? responses[2].data.results : [];

                                let prompts = PromptService.processPromptValues({
                                    launchConf: responses[1].data,
                                    launchOptions: responses[0].data,
                                    currentValues: $scope.nodeBeingEdited.originalNodeObj
                                });

                                let defaultCredsWithoutOverrides = [];

                                prompts.credentials.previousOverrides = _.cloneDeep(workflowNodeCredentials);

                                const credentialHasScheduleOverride = (templateDefaultCred) => {
                                    let credentialHasOverride = false;
                                    workflowNodeCredentials.forEach((scheduleCred) => {
                                        if (templateDefaultCred.credential_type === scheduleCred.credential_type) {
                                            if (
                                                (!templateDefaultCred.vault_id && !scheduleCred.inputs.vault_id) ||
                                                (templateDefaultCred.vault_id && scheduleCred.inputs.vault_id && templateDefaultCred.vault_id === scheduleCred.inputs.vault_id)
                                            ) {
                                                credentialHasOverride = true;
                                            }
                                        }
                                    });

                                    return credentialHasOverride;
                                };

                                if (_.has(launchConf, 'defaults.credentials')) {
                                    launchConf.defaults.credentials.forEach((defaultCred) => {
                                        if (!credentialHasScheduleOverride(defaultCred)) {
                                            defaultCredsWithoutOverrides.push(defaultCred);
                                        }
                                    });
                                }

                                prompts.credentials.value = workflowNodeCredentials.concat(defaultCredsWithoutOverrides);

                                if ($scope.nodeBeingEdited.unifiedJobTemplate.unified_job_template === 'job') {
                                    if ((!$scope.nodeBeingEdited.unifiedJobTemplate.inventory && !launchConf.ask_inventory_on_launch) || !$scope.nodeBeingEdited.unifiedJobTemplate.project) {
                                        $scope.selectedTemplateInvalid = true;
                                    } else {
                                        $scope.selectedTemplateInvalid = false;
                                    }
                                } else {
                                    $scope.selectedTemplateInvalid = false;
                                }

                                let credentialRequiresPassword = false;

                                prompts.credentials.value.forEach((credential) => {
                                    if (credential.inputs) {
                                        if ((credential.inputs.password && credential.inputs.password === "ASK") ||
                                            (credential.inputs.become_password && credential.inputs.become_password === "ASK") ||
                                            (credential.inputs.ssh_key_unlock && credential.inputs.ssh_key_unlock === "ASK") ||
                                            (credential.inputs.vault_password && credential.inputs.vault_password === "ASK")
                                        ) {
                                            credentialRequiresPassword = true;
                                        }
                                    } else if (credential.passwords_needed && credential.passwords_needed.length > 0) {
                                        credentialRequiresPassword = true;
                                    }
                                });

                                $scope.credentialRequiresPassword = credentialRequiresPassword;

                                if (!launchConf.survey_enabled &&
                                    !launchConf.ask_inventory_on_launch &&
                                    !launchConf.ask_credential_on_launch &&
                                    !launchConf.ask_verbosity_on_launch &&
                                    !launchConf.ask_job_type_on_launch &&
                                    !launchConf.ask_limit_on_launch &&
                                    !launchConf.ask_tags_on_launch &&
                                    !launchConf.ask_skip_tags_on_launch &&
                                    !launchConf.ask_diff_mode_on_launch &&
                                    !launchConf.credential_needed_to_start &&
                                    !launchConf.ask_variables_on_launch &&
                                    launchConf.variables_needed_to_start.length === 0) {
                                    $scope.showPromptButton = false;
                                    $scope.promptModalMissingReqFields = false;
                                } else {
                                    $scope.showPromptButton = true;

                                    if (launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory') && !_.has($scope, 'nodeBeingEdited.originalNodeObj.summary_fields.inventory')) {
                                        $scope.promptModalMissingReqFields = true;
                                    } else {
                                        $scope.promptModalMissingReqFields = false;
                                    }

                                    if (responses[1].data.survey_enabled) {
                                        // go out and get the survey questions
                                        jobTemplate.getSurveyQuestions($scope.nodeBeingEdited.unifiedJobTemplate.id)
                                            .then((surveyQuestionRes) => {

                                                let processed = PromptService.processSurveyQuestions({
                                                    surveyQuestions: surveyQuestionRes.data.spec,
                                                    extra_data: _.cloneDeep($scope.nodeBeingEdited.originalNodeObj.extra_data)
                                                });

                                                $scope.missingSurveyValue = processed.missingSurveyValue;

                                                $scope.extraVars = (processed.extra_data === '' || _.isEmpty(processed.extra_data)) ? '---' : '---\n' + jsyaml.safeDump(processed.extra_data);

                                                $scope.nodeBeingEdited.promptData = $scope.promptData = {
                                                    launchConf: launchConf,
                                                    launchOptions: launchOptions,
                                                    prompts: prompts,
                                                    surveyQuestions: surveyQuestionRes.data.spec,
                                                    template: $scope.nodeBeingEdited.unifiedJobTemplate.id
                                                };

                                                surveyQuestionWatcher = $scope.$watch('promptData.surveyQuestions', () => {
                                                    let missingSurveyValue = false;
                                                    _.each($scope.promptData.surveyQuestions, (question) => {
                                                        if (question.required && (Empty(question.model) || question.model === [])) {
                                                            missingSurveyValue = true;
                                                        }
                                                    });
                                                    $scope.missingSurveyValue = missingSurveyValue;
                                                }, true);

                                                checkCredentialsForRequiredPasswords();

                                                watchForPromptChanges();
                                            });
                                    } else {
                                        $scope.nodeBeingEdited.promptData = $scope.promptData = {
                                            launchConf: launchConf,
                                            launchOptions: launchOptions,
                                            prompts: prompts,
                                            template: $scope.nodeBeingEdited.unifiedJobTemplate.id
                                        };

                                        checkCredentialsForRequiredPasswords();

                                        watchForPromptChanges();
                                    }
                                }
                            });
                    }

                    if (_.get($scope, 'nodeBeingEdited.unifiedJobTemplate')) {

                        if (_.get($scope, 'nodeBeingEdited.unifiedJobTemplate.type') === "job_template" ||
                            _.get($scope, 'nodeBeingEdited.unifiedJobTemplate.type') === "workflow_job_template") {
                            $scope.workflowMakerFormConfig.activeTab = "jobs";
                        }

                        $scope.selectedTemplate = $scope.nodeBeingEdited.unifiedJobTemplate;

                        if ($scope.selectedTemplate.unified_job_type) {
                            switch ($scope.selectedTemplate.unified_job_type) {
                                case "job":
                                case "workflow_job":
                                    $scope.workflowMakerFormConfig.activeTab = "jobs";
                                    break;
                                case "project_update":
                                    $scope.workflowMakerFormConfig.activeTab = "project_sync";
                                    break;
                                case "inventory_update":
                                    $scope.workflowMakerFormConfig.activeTab = "inventory_sync";
                                    break;
                            }
                        } else if ($scope.selectedTemplate.type) {
                            switch ($scope.selectedTemplate.type) {
                                case "job_template":
                                case "workflow_job_template":
                                    $scope.workflowMakerFormConfig.activeTab = "jobs";
                                    break;
                                case "project":
                                    $scope.workflowMakerFormConfig.activeTab = "project_sync";
                                    break;
                                case "inventory_source":
                                    $scope.workflowMakerFormConfig.activeTab = "inventory_sync";
                                    break;
                            }
                        }
                    } else {
                        $scope.workflowMakerFormConfig.activeTab = "jobs";
                    }

                    let edgeDropdownOptions = null;

                    // Select RUN dropdown option
                    switch ($scope.nodeBeingEdited.edgeType) {
                        case "always":
                            $scope.edgeType = {
                                label: $scope.strings.get('workflow_maker.ALWAYS'),
                                value: "always"
                            };
                            if ($scope.nodeBeingEdited.isRoot) {
                                edgeDropdownOptions = 'always';
                            }
                            break;
                        case "success":
                            $scope.edgeType = {
                                label: $scope.strings.get('workflow_maker.ON_SUCCESS'),
                                value: "success"
                            };
                            break;
                        case "failure":
                            $scope.edgeType = {
                                label: $scope.strings.get('workflow_maker.ON_FAILURE'),
                                value: "failure"
                            };
                            break;
                    }

                    $timeout(updateEdgeDropdownOptions(edgeDropdownOptions));

                    $scope.$broadcast("refreshWorkflowChart");
                };

                // Determine whether or not we need to go out and GET this nodes unified job template
                // in order to determine whether or not prompt fields are needed
                if (!$scope.nodeBeingEdited.isNew && !$scope.nodeBeingEdited.edited &&
                    (_.get($scope, 'nodeBeingEdited.unifiedJobTemplate.unified_job_type') === 'job' ||
                        _.get($scope, 'nodeBeingEdited.unifiedJobTemplate.unified_job_type') === 'workflow_job')) {
                    // This is a node that we got back from the api with an incomplete
                    // unified job template so we're going to pull down the whole object

                    TemplatesService.getUnifiedJobTemplate($scope.nodeBeingEdited.unifiedJobTemplate.id)
                        .then(function (data) {
                            $scope.nodeBeingEdited.unifiedJobTemplate = _.clone(data.data.results[0]);
                            finishConfiguringEdit();
                        }, function ({
                            data,
                            status,
                            config
                        }) {
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
                    finishConfiguringEdit();
                }

            }

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

                // TODO: turn this into a promise so that we can handle errors

                WorkflowService.removeNodeFromTree({
                    tree: $scope.treeData.data,
                    nodeToBeDeleted: $scope.nodeToBeDeleted
                });

                if ($scope.nodeToBeDeleted.isNew !== true) {
                    $scope.treeData.data.deletedNodes.push($scope.nodeToBeDeleted.nodeId);
                }

                if ($scope.nodeToBeDeleted.isActiveEdit) {
                    resetNodeForm();
                }

                resetDeleteNode();

                $scope.$broadcast("refreshWorkflowChart");

                if ($scope.placeholderNode) {
                    let edgeType = {
                        label: $scope.strings.get('workflow_maker.ON_SUCCESS'),
                        value: "success"
                    };

                    if ($scope.placeholderNode.isRoot) {
                        updateEdgeDropdownOptions('always');
                        edgeType = {
                            label: $scope.strings.get('workflow_maker.ALWAYS'),
                            value: "always"
                        };
                    } else {
                        updateEdgeDropdownOptions();
                    }

                    $scope.edgeType = edgeType;
                } else if ($scope.nodeBeingEdited) {

                    switch ($scope.nodeBeingEdited.edgeType) {
                        case "always":
                            $scope.edgeType = {
                                label: $scope.strings.get('workflow_maker.ALWAYS'),
                                value: "always"
                            };
                            if ($scope.nodeBeingEdited.isRoot) {
                                updateEdgeDropdownOptions('always');
                            } else {
                                updateEdgeDropdownOptions();
                            }
                            break;
                        case "success":
                            $scope.edgeType = {
                                label: $scope.strings.get('workflow_maker.ON_SUCCESS'),
                                value: "success"
                            };
                            updateEdgeDropdownOptions();
                            break;
                        case "failure":
                            $scope.edgeType = {
                                label: $scope.strings.get('workflow_maker.ON_FAILURE'),
                                value: "failure"
                            };
                            updateEdgeDropdownOptions();
                            break;
                    }
                }

                $scope.treeData.data.totalNodes--;
            }

        };

        $scope.toggleFormTab = function (tab) {
            if ($scope.workflowMakerFormConfig.activeTab !== tab) {
                $scope.workflowMakerFormConfig.activeTab = tab;
            }
        };

        $scope.templateManuallySelected = function (selectedTemplate) {

            if (promptWatcher) {
                promptWatcher();
            }

            if (surveyQuestionWatcher) {
                surveyQuestionWatcher();
            }

            if (credentialsWatcher) {
                credentialsWatcher();
            }

            $scope.promptData = null;
            if (selectedTemplate.type === "job_template" || selectedTemplate.type === "workflow_job_template") {
                let jobTemplate = selectedTemplate.type === "workflow_job_template" ? new WorkflowJobTemplate() : new JobTemplate();

                $q.all([jobTemplate.optionsLaunch(selectedTemplate.id), jobTemplate.getLaunch(selectedTemplate.id)])
                    .then((responses) => {
                        let launchConf = responses[1].data;
                        if (selectedTemplate.type === 'job_template') {
                            if ((!selectedTemplate.inventory && !launchConf.ask_inventory_on_launch) || !selectedTemplate.project) {
                                $scope.selectedTemplateInvalid = true;
                            } else {
                                $scope.selectedTemplateInvalid = false;
                            }

                            if (launchConf.passwords_needed_to_start && launchConf.passwords_needed_to_start.length > 0) {
                                $scope.credentialRequiresPassword = true;
                            } else {
                                $scope.credentialRequiresPassword = false;
                            }
                        }

                        $scope.selectedTemplate = angular.copy(selectedTemplate);

                        if (!launchConf.survey_enabled &&
                            !launchConf.ask_inventory_on_launch &&
                            !launchConf.ask_credential_on_launch &&
                            !launchConf.ask_verbosity_on_launch &&
                            !launchConf.ask_job_type_on_launch &&
                            !launchConf.ask_limit_on_launch &&
                            !launchConf.ask_tags_on_launch &&
                            !launchConf.ask_skip_tags_on_launch &&
                            !launchConf.ask_diff_mode_on_launch &&
                            !launchConf.credential_needed_to_start &&
                            !launchConf.ask_variables_on_launch &&
                            launchConf.variables_needed_to_start.length === 0) {
                            $scope.showPromptButton = false;
                            $scope.promptModalMissingReqFields = false;
                        } else {
                            $scope.showPromptButton = true;

                            if (selectedTemplate.type === 'job_template') {
                                if (launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory')) {
                                    $scope.promptModalMissingReqFields = true;
                                } else {
                                    $scope.promptModalMissingReqFields = false;
                                }
                            } else {
                                $scope.promptModalMissingReqFields = false;
                            }

                            if (launchConf.survey_enabled) {
                                // go out and get the survey questions
                                jobTemplate.getSurveyQuestions(selectedTemplate.id)
                                    .then((surveyQuestionRes) => {

                                        let processed = PromptService.processSurveyQuestions({
                                            surveyQuestions: surveyQuestionRes.data.spec
                                        });

                                        $scope.missingSurveyValue = processed.missingSurveyValue;

                                        $scope.promptData = {
                                            launchConf: responses[1].data,
                                            launchOptions: responses[0].data,
                                            surveyQuestions: processed.surveyQuestions,
                                            template: selectedTemplate.id,
                                            prompts: PromptService.processPromptValues({
                                                launchConf: responses[1].data,
                                                launchOptions: responses[0].data
                                            }),
                                        };

                                        surveyQuestionWatcher = $scope.$watch('promptData.surveyQuestions', () => {
                                            let missingSurveyValue = false;
                                            _.each($scope.promptData.surveyQuestions, (question) => {
                                                if (question.required && (Empty(question.model) || question.model === [])) {
                                                    missingSurveyValue = true;
                                                }
                                            });
                                            $scope.missingSurveyValue = missingSurveyValue;
                                        }, true);

                                        watchForPromptChanges();
                                    });
                            } else {
                                $scope.promptData = {
                                    launchConf: responses[1].data,
                                    launchOptions: responses[0].data,
                                    template: selectedTemplate.id,
                                    prompts: PromptService.processPromptValues({
                                        launchConf: responses[1].data,
                                        launchOptions: responses[0].data
                                    }),
                                };

                                watchForPromptChanges();
                            }
                        }
                    });
            } else {
                $scope.selectedTemplate = angular.copy(selectedTemplate);
                $scope.selectedTemplateInvalid = false;
                $scope.showPromptButton = false;
                $scope.promptModalMissingReqFields = false;
            }
        };

        $scope.toggleManualControls = function () {
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

        $scope.openPromptModal = function () {
            $scope.promptData.triggerModalOpen = true;
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
                }, function ({
                    data,
                    status,
                    config
                }) {
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

        updateEdgeDropdownOptions();
    }
];
