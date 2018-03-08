/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'WorkflowService', 'GetBasePath', 'TemplatesService',
    '$state', 'ProcessErrors', 'CreateSelect2', 'WorkflowMakerForm', '$q', 'JobTemplateModel',
    'Empty', 'PromptService', 'Rest',
    function($scope, WorkflowService, GetBasePath, TemplatesService, $state,
    ProcessErrors, CreateSelect2, WorkflowMakerForm, $q, JobTemplate,
    Empty, PromptService, Rest) {

        let form = WorkflowMakerForm();
        let promptWatcher;

        $scope.workflowMakerFormConfig = {
            nodeMode: "idle",
            activeTab: "jobs",
            formIsValid: false
        };

        $scope.job_type_options = [{
            label: "Run",
            value: "run"
        }, {
            label: "Check",
            value: "check"
        }];

        $scope.edgeFlags = {
             conflict: false
         };

         $scope.edgeTypeOptions = [
             {
                 label: 'Always',
                 value: 'always'
             },
             {
                 label: 'On Success',
                 value: 'success'
             },
             {
                 label: 'On Failure',
                 value: 'failure'
             }
         ];

        let editRequests = [];
        let associateRequests = [];
        let disassociateRequests = [];
        let credentialRequests = [];

        $scope.showKey = false;
        $scope.toggleKey = () => $scope.showKey = !$scope.showKey;
        $scope.keyClassList = `{ 'Key-menuIcon--active': showKey }`;

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

            let buildSendableNodeData = function() {
                // Create the node
                let sendableNodeData = {
                    unified_job_template: params.node.unifiedJobTemplate.id
                };

                // Check to see if the user has provided any prompt values that are different
                // from the defaults in the job template

                if(params.node.unifiedJobTemplate.type === "job_template" && params.node.promptData) {
                    if(params.node.promptData.launchConf.survey_enabled){
                        for (var i=0; i < params.node.promptData.surveyQuestions.length; i++){
                            var fld = params.node.promptData.surveyQuestions[i].variable;
                            // grab all survey questions that have answers
                            if(params.node.promptData.surveyQuestions[i].required || (params.node.promptData.surveyQuestions[i].required === false && params.node.promptData.surveyQuestions[i].model.toString()!=="")) {
                                if(!sendableNodeData.extra_data) {
                                    sendableNodeData.extra_data = {};
                                }
                                sendableNodeData.extra_data[fld] = params.node.promptData.surveyQuestions[i].model;
                            }

                            if(params.node.promptData.surveyQuestions[i].required === false && _.isEmpty(params.node.promptData.surveyQuestions[i].model)) {
                                switch (params.node.promptData.surveyQuestions[i].type) {
                                    // for optional text and text-areas, submit a blank string if min length is 0
                                    // -- this is confusing, for an explanation see:
                                    //    http://docs.ansible.com/ansible-tower/latest/html/userguide/job_templates.html#optional-survey-questions
                                    //
                                    case "text":
                                    case "textarea":
                                    if (params.node.promptData.surveyQuestions[i].min === 0) {
                                        sendableNodeData.extra_data[fld] = "";
                                    }
                                    break;
                                }
                            }
                        }
                    }

                    if(_.has(params, 'node.promptData.prompts.jobType.value.value') && _.get(params, 'node.promptData.launchConf.ask_job_type_on_launch')) {
                        sendableNodeData.job_type = params.node.promptData.prompts.jobType.templateDefault === params.node.promptData.prompts.jobType.value.value ? null : params.node.promptData.prompts.jobType.value.value;
                    }
                    if(_.has(params, 'node.promptData.prompts.tags.value') && _.get(params, 'node.promptData.launchConf.ask_tags_on_launch')){
                        let templateDefaultJobTags = params.node.promptData.prompts.tags.templateDefault.split(',');
                        sendableNodeData.job_tags = (_.isEqual(templateDefaultJobTags.sort(), params.node.promptData.prompts.tags.value.map(a => a.value).sort())) ? null : params.node.promptData.prompts.tags.value.map(a => a.value).join();
                    }
                    if(_.has(params, 'node.promptData.prompts.skipTags.value') && _.get(params, 'node.promptData.launchConf.ask_skip_tags_on_launch')){
                        let templateDefaultSkipTags = params.node.promptData.prompts.skipTags.templateDefault.split(',');
                        sendableNodeData.skip_tags = (_.isEqual(templateDefaultSkipTags.sort(), params.node.promptData.prompts.skipTags.value.map(a => a.value).sort())) ? null : params.node.promptData.prompts.skipTags.value.map(a => a.value).join();
                    }
                    if(_.has(params, 'node.promptData.prompts.limit.value') && _.get(params, 'node.promptData.launchConf.ask_limit_on_launch')){
                        sendableNodeData.limit = params.node.promptData.prompts.limit.templateDefault === params.node.promptData.prompts.limit.value ? null : params.node.promptData.prompts.limit.value;
                    }
                    if(_.has(params, 'node.promptData.prompts.verbosity.value.value') && _.get(params, 'node.promptData.launchConf.ask_verbosity_on_launch')){
                        sendableNodeData.verbosity = params.node.promptData.prompts.verbosity.templateDefault === params.node.promptData.prompts.verbosity.value.value ? null : params.node.promptData.prompts.verbosity.value.value;
                    }
                    if(_.has(params, 'node.promptData.prompts.inventory.value') && _.get(params, 'node.promptData.launchConf.ask_inventory_on_launch')){
                        sendableNodeData.inventory = _.has(params, 'node.promptData.prompts.inventory.templateDefault.id') && params.node.promptData.prompts.inventory.templateDefault.id === params.node.promptData.prompts.inventory.value.id ? null : params.node.promptData.prompts.inventory.value.id;
                    }
                    if(_.has(params, 'node.promptData.prompts.diffMode.value') && _.get(params, 'node.promptData.launchConf.ask_diff_mode_on_launch')){
                        sendableNodeData.diff_mode = params.node.promptData.prompts.diffMode.templateDefault === params.node.promptData.prompts.diffMode.value ? null : params.node.promptData.prompts.diffMode.value;
                    }
                }

                return sendableNodeData;
            };

            let continueRecursing = function(parentId) {
                $scope.totalIteratedNodes++;

                if($scope.totalIteratedNodes === $scope.treeData.data.totalNodes) {
                    // We're done recursing, lets move on
                    completionCallback();
                }
                else {
                    if(params.node.children && params.node.children.length > 0) {
                        _.forEach(params.node.children, function(child) {
                            if(child.edgeType === "success") {
                                recursiveNodeUpdates({
                                    parentId: parentId,
                                    node: child
                                }, completionCallback);
                            }
                            else if(child.edgeType === "failure") {
                                recursiveNodeUpdates({
                                    parentId: parentId,
                                    node: child
                                }, completionCallback);
                            }
                            else if(child.edgeType === "always") {
                                recursiveNodeUpdates({
                                    parentId: parentId,
                                    node: child
                                }, completionCallback);
                            }
                        });
                    }
                }
            };

            if(params.node.isNew) {

                TemplatesService.addWorkflowNode({
                    url: $scope.treeData.workflow_job_template_obj.related.workflow_nodes,
                    data: buildSendableNodeData()
                })
                .then(function(data) {

                    if(!params.node.isRoot) {
                        associateRequests.push({
                            parentId: params.parentId,
                            nodeId: data.data.id,
                            edge: params.node.edgeType
                        });
                    }

                    if(_.get(params, 'node.promptData.launchConf.ask_credential_on_launch')){
                         // This finds the credentials that were selected in the prompt but don't occur
                         // in the template defaults
                         let credentialsToPost = params.node.promptData.prompts.credentials.value.filter(function(credFromPrompt) {
                             let defaultCreds = params.node.promptData.launchConf.defaults.credentials ? params.node.promptData.launchConf.defaults.credentials : [];
                             return !defaultCreds.some(function(defaultCred) {
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
                }, function(error) {
                    ProcessErrors($scope, error.data, error.status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to add workflow node. ' +
                        'POST returned status: ' +
                        error.status
                    });
                });
            }
            else {
                if(params.node.edited || !params.node.originalParentId || (params.node.originalParentId && params.parentId !== params.node.originalParentId)) {

                    if(params.node.edited) {

                        editRequests.push({
                            id: params.node.nodeId,
                            data: buildSendableNodeData()
                        });

                        if(_.get(params, 'node.promptData.launchConf.ask_credential_on_launch')){
                             let credentialsNotInPriorCredentials = params.node.promptData.prompts.credentials.value.filter(function(credFromPrompt) {
                                 let defaultCreds = params.node.promptData.launchConf.defaults.credentials ? params.node.promptData.launchConf.defaults.credentials : [];
                                 return !defaultCreds.some(function(defaultCred) {
                                     return credFromPrompt.id === defaultCred.id;
                                 });
                             });

                             let credentialsToAdd = credentialsNotInPriorCredentials.filter(function(credNotInPrior) {
                                 return !params.node.promptData.prompts.credentials.previousOverrides.some(function(priorCred) {
                                     return credNotInPrior.id === priorCred.id;
                                 });
                             });

                             let credentialsToRemove = params.node.promptData.prompts.credentials.previousOverrides.filter(function(priorCred) {
                                 return !credentialsNotInPriorCredentials.some(function(credNotInPrior) {
                                     return priorCred.id === credNotInPrior.id;
                                 });
                             });

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

                    if((params.node.originalParentId && params.parentId !== params.node.originalParentId) || params.node.originalEdge !== params.node.edgeType) {//beep

                        let parentIsDeleted = false;

                        _.forEach($scope.treeData.data.deletedNodes, function(deletedNode) {
                            if(deletedNode === params.node.originalParentId) {
                                parentIsDeleted = true;
                            }
                        });

                        if(!parentIsDeleted) {
                            disassociateRequests.push({
                                parentId: params.node.originalParentId,
                                nodeId: params.node.nodeId,
                                edge: params.node.originalEdge
                            });
                        }

                        // Can only associate if we have a parent.
                        // If we don't have a parent then this is a root node
                        // and the act of disassociating will make it a root node
                        if(params.parentId) {
                            associateRequests.push({
                                parentId: params.parentId,
                                nodeId: params.node.nodeId,
                                edge: params.node.edgeType
                            });
                        }

                    }
                    else if(!params.node.originalParentId && params.parentId) {
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

        let updateEdgeDropdownOptions = (optionsToInclude) => {
            // Not passing optionsToInclude will include all by default
            if(!optionsToInclude) {
                $scope.edgeTypeOptions = [
                    {
                        label: 'Always',
                        value: 'always'
                    },
                    {
                        label: 'On Success',
                        value: 'success'
                    },
                    {
                        label: 'On Failure',
                        value: 'failure'
                    }
                ];
            } else {
                $scope.edgeTypeOptions = [];

                optionsToInclude.forEach((optionToInclude) => {
                    if(optionToInclude === "always") {
                        $scope.edgeTypeOptions.push({
                            label: 'Always',
                            value: 'always'
                        });
                    } else if(optionToInclude === "success") {
                        $scope.edgeTypeOptions.push({
                            label: 'On Success',
                            value: 'success'
                        });
                    } else if(optionToInclude === "failure") {
                        $scope.edgeTypeOptions.push({
                            label: 'On Failure',
                            value: 'failure'
                        });
                    }
                });
            }

            CreateSelect2({
                element: '#workflow_node_edge',
                multiple: false
            });
        };

        let watchForPromptChanges = () => {
            let promptDataToWatch = [
                'promptData.prompts.inventory.value',
                'promptData.prompts.verbosity.value',
                'missingSurveyValue'
            ];

            promptWatcher = $scope.$watchGroup(promptDataToWatch, function() {
                let missingPromptValue = false;
                if($scope.missingSurveyValue) {
                    missingPromptValue = true;
                } else if(!$scope.promptData.prompts.inventory.value || !$scope.promptData.prompts.inventory.value.id) {
                    missingPromptValue = true;
                }
                $scope.promptModalMissingReqFields = missingPromptValue;
            });
        };

        $scope.closeWorkflowMaker = function() {
            // Revert the data to the master which was created when the dialog was opened
            $scope.treeData.data = angular.copy($scope.treeDataMaster);
            $scope.closeDialog();
        };

        $scope.saveWorkflowMaker = function() {

            $scope.totalIteratedNodes = 0;

            if($scope.treeData && $scope.treeData.data && $scope.treeData.data.children && $scope.treeData.data.children.length > 0) {
                let completionCallback = function() {

                    let disassociatePromises = disassociateRequests.map(function(request) {
                        return TemplatesService.disassociateWorkflowNode({
                            parentId: request.parentId,
                            nodeId: request.nodeId,
                            edge: request.edge
                        });
                    });

                    let credentialPromises = credentialRequests.map(function(request) {
                        return TemplatesService.postWorkflowNodeCredential({
                            id: request.id,
                            data: request.data
                        });
                    });

                    let editNodePromises = editRequests.map(function(request) {
                        return TemplatesService.editWorkflowNode({
                            id: request.id,
                            data: request.data
                        });
                    });

                    let deletePromises = $scope.treeData.data.deletedNodes.map(function(nodeId) {
                        return TemplatesService.deleteWorkflowJobTemplateNode(nodeId);
                    });

                    $q.all(disassociatePromises.concat(editNodePromises, deletePromises, credentialPromises))
                    .then(function() {

                        let associatePromises = associateRequests.map(function(request) {
                            return TemplatesService.associateWorkflowNode({
                                parentId: request.parentId,
                                nodeId: request.nodeId,
                                edge: request.edge
                            });
                        });

                        $q.all(associatePromises)
                        .then(function() {
                            $scope.closeDialog();
                        });
                    });
                };

                _.forEach($scope.treeData.data.children, function(child) {
                    recursiveNodeUpdates({
                        node: child
                    }, completionCallback);
                });
            }
            else {

                let deletePromises = $scope.treeData.data.deletedNodes.map(function(nodeId) {
                    return TemplatesService.deleteWorkflowJobTemplateNode(nodeId);
                });

                $q.all(deletePromises)
                .then(function() {
                    $scope.closeDialog();
                });
            }
        };

        /* ADD NODE FUNCTIONS */

        $scope.startAddNode = function(parent, betweenTwoNodes) {

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

            let siblingConnectionTypes = WorkflowService.getSiblingConnectionTypes({
                tree: $scope.treeData.data,
                parentId: betweenTwoNodes ? parent.source.id : parent.id,
                childId: $scope.placeholderNode.id
            });

            // Set the default to success
            let edgeType = {label: "On Success", value: "success"};

            if (parent && ((betweenTwoNodes && parent.source.isStartNode) || (!betweenTwoNodes && parent.isStartNode))) {
                // We don't want to give the user the option to select
                // a type as this node will always be executed
                updateEdgeDropdownOptions(["always"]);
                edgeType = {label: "Always", value: "always"};
            } else {
                if (_.includes(siblingConnectionTypes, "success") || _.includes(siblingConnectionTypes, "failure")) {
                    updateEdgeDropdownOptions(["success", "failure"]);
                    edgeType = {label: "On Success", value: "success"};
                } else if (_.includes(siblingConnectionTypes, "always")) {
                    updateEdgeDropdownOptions(["always"]);
                    edgeType = {label: "Always", value: "always"};
                } else {
                    updateEdgeDropdownOptions();
                }
            }

            // Reset the edgeConflict flag
            resetEdgeConflict();

            $scope.edgeType = edgeType;
            $scope.$broadcast("refreshWorkflowChart");

        };

        $scope.confirmNodeForm = function() {
            if ($scope.workflowMakerFormConfig.nodeMode === "add") {
                if ($scope.selectedTemplate && $scope.edgeType && $scope.edgeType.value) {

                    $scope.placeholderNode.unifiedJobTemplate = $scope.selectedTemplate;
                    $scope.placeholderNode.edgeType = $scope.edgeType.value;
                    if ($scope.placeholderNode.unifiedJobTemplate.type === 'job_template') {
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

                    if ($scope.nodeBeingEdited.unifiedJobTemplate.type === 'job_template') {
                        $scope.nodeBeingEdited.promptData = _.cloneDeep($scope.promptData);
                    }

                    $scope.nodeBeingEdited.isActiveEdit = false;

                    $scope.nodeBeingEdited.edited = true;

                    resetNodeForm();
                }
            }

            if(promptWatcher) {
                promptWatcher();
            }

            $scope.promptData = null;

            // Reset the edgeConflict flag
            resetEdgeConflict();

            $scope.$broadcast("refreshWorkflowChart");
        };

        $scope.cancelNodeForm = function() {
            if ($scope.workflowMakerFormConfig.nodeMode === "add") {
                // Remove the placeholder node from the tree
                WorkflowService.removeNodeFromTree({
                    tree: $scope.treeData.data,
                    nodeToBeDeleted: $scope.placeholderNode
                });
            } else if ($scope.workflowMakerFormConfig.nodeMode === "edit") {
                $scope.nodeBeingEdited.isActiveEdit = false;
            }

            if(promptWatcher) {
                promptWatcher();
            }

            $scope.promptData = null;

            // Reset the edgeConflict flag
            resetEdgeConflict();

            // Reset the form
            resetNodeForm();

            $scope.$broadcast("refreshWorkflowChart");
        };

        /* EDIT NODE FUNCTIONS */

        $scope.startEditNode = function(nodeToEdit) {

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

                let finishConfiguringEdit = function() {

                    let jobTemplate = new JobTemplate();

                    Rest.setUrl($scope.nodeBeingEdited.originalNodeObj.related.credentials);

                    if($scope.nodeBeingEdited.promptData) {
                        $scope.promptData = _.cloneDeep($scope.nodeBeingEdited.promptData);
                    }else if($scope.nodeBeingEdited.unifiedJobTemplate){
                        $q.all([jobTemplate.optionsLaunch($scope.nodeBeingEdited.unifiedJobTemplate.id), jobTemplate.getLaunch($scope.nodeBeingEdited.unifiedJobTemplate.id), Rest.get()])
                            .then((responses) => {
                                let launchOptions = responses[0].data,
                                    launchConf = responses[1].data,
                                    workflowNodeCredentials = responses[2].data.results;

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
                                        if(templateDefaultCred.credential_type === scheduleCred.credential_type) {
                                            if(
                                                (!templateDefaultCred.vault_id && !scheduleCred.inputs.vault_id) ||
                                                (templateDefaultCred.vault_id && scheduleCred.inputs.vault_id && templateDefaultCred.vault_id === scheduleCred.inputs.vault_id)
                                            ) {
                                                credentialHasOverride = true;
                                            }
                                        }
                                    });

                                    return credentialHasOverride;
                                };

                                if(_.has(launchConf, 'defaults.credentials')) {
                                    launchConf.defaults.credentials.forEach((defaultCred) => {
                                        if(!credentialHasScheduleOverride(defaultCred)) {
                                            defaultCredsWithoutOverrides.push(defaultCred);
                                        }
                                    });
                                }

                                prompts.credentials.value = workflowNodeCredentials.concat(defaultCredsWithoutOverrides);

                                if(!launchConf.survey_enabled &&
                                    !launchConf.ask_inventory_on_launch &&
                                    !launchConf.ask_credential_on_launch &&
                                    !launchConf.ask_verbosity_on_launch &&
                                    !launchConf.ask_job_type_on_launch &&
                                    !launchConf.ask_limit_on_launch &&
                                    !launchConf.ask_tags_on_launch &&
                                    !launchConf.ask_skip_tags_on_launch &&
                                    !launchConf.ask_diff_mode_on_launch &&
                                    !launchConf.survey_enabled &&
                                    !launchConf.credential_needed_to_start &&
                                    !launchConf.inventory_needed_to_start &&
                                    launchConf.passwords_needed_to_start.length === 0 &&
                                    launchConf.variables_needed_to_start.length === 0) {
                                        $scope.showPromptButton = false;
                                } else {
                                    $scope.showPromptButton = true;

                                    if(launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory') && !_.has($scope, 'nodeBeingEdited.originalNodeObj.summary_fields.inventory')) {
                                        $scope.promptModalMissingReqFields = true;
                                    }

                                    if(responses[1].data.survey_enabled) {
                                        // go out and get the survey questions
                                        jobTemplate.getSurveyQuestions($scope.nodeBeingEdited.unifiedJobTemplate.id)
                                            .then((surveyQuestionRes) => {

                                                let processed = PromptService.processSurveyQuestions({
                                                    surveyQuestions: surveyQuestionRes.data.spec,
                                                    extra_data: $scope.nodeBeingEdited.originalNodeObj.extra_data
                                                });

                                                $scope.missingSurveyValue = processed.missingSurveyValue;

                                                $scope.extraVars = (processed.extra_data === '' || _.isEmpty(processed.extra_data)) ? '---' : '---\n' + jsyaml.safeDump(processed.extra_data);

                                                $scope.promptData = {
                                                    launchConf: launchConf,
                                                    launchOptions: launchOptions,
                                                    prompts: prompts,
                                                    surveyQuestions: surveyQuestionRes.data.spec,
                                                    template: $scope.nodeBeingEdited.unifiedJobTemplate.id
                                                };

                                                $scope.$watch('promptData.surveyQuestions', () => {
                                                    let missingSurveyValue = false;
                                                    _.each($scope.promptData.surveyQuestions, (question) => {
                                                        if(question.required && (Empty(question.model) || question.model === [])) {
                                                            missingSurveyValue = true;
                                                        }
                                                    });
                                                    $scope.missingSurveyValue = missingSurveyValue;
                                                }, true);

                                                watchForPromptChanges();
                                            });
                                    }
                                    else {
                                        $scope.promptData = {
                                            launchConf: launchConf,
                                            launchOptions: launchOptions,
                                            prompts: prompts,
                                            template: $scope.nodeBeingEdited.unifiedJobTemplate.id
                                        };
                                        watchForPromptChanges();
                                    }
                                }
                        });

                        if ($scope.nodeBeingEdited.unifiedJobTemplate.type === "job_template") {
                            $scope.workflowMakerFormConfig.activeTab = "jobs";
                        }

                        $scope.selectedTemplate = $scope.nodeBeingEdited.unifiedJobTemplate;

                        if($scope.selectedTemplate.unified_job_type) {
                            switch ($scope.selectedTemplate.unified_job_type) {
                                case "job":
                                    $scope.workflowMakerFormConfig.activeTab = "jobs";
                                    break;
                                case "project_update":
                                    $scope.workflowMakerFormConfig.activeTab = "project_sync";
                                    break;
                                case "inventory_update":
                                    $scope.workflowMakerFormConfig.activeTab = "inventory_sync";
                                    break;
                            }
                        }
                        else if($scope.selectedTemplate.type) {
                            switch ($scope.selectedTemplate.type) {
                                case "job_template":
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

                    }

                    let siblingConnectionTypes = WorkflowService.getSiblingConnectionTypes({
                         tree: $scope.treeData.data,
                         parentId: parent.id,
                         childId: nodeToEdit.id
                     });

                     let edgeDropdownOptions = null;

                     switch($scope.nodeBeingEdited.edgeType) {
                        case "always":
                            $scope.edgeType = {label: "Always", value: "always"};
                            if(siblingConnectionTypes.length === 0 || (siblingConnectionTypes.length === 1 && _.includes(siblingConnectionTypes, "always"))) {
                                edgeDropdownOptions = ["always"];
                            }
                            break;
                        case "success":
                            $scope.edgeType = {label: "On Success", value: "success"};
                            if(siblingConnectionTypes.length === 0 || (!_.includes(siblingConnectionTypes, "always"))) {
                                edgeDropdownOptions = ["success", "failure"];
                            }
                            break;
                        case "failure":
                            $scope.edgeType = {label: "On Failure", value: "failure"};
                            if(siblingConnectionTypes.length === 0 || (!_.includes(siblingConnectionTypes, "always"))) {
                                edgeDropdownOptions = ["success", "failure"];
                            }
                            break;
                    }

                    updateEdgeDropdownOptions(edgeDropdownOptions);

                    $scope.$broadcast("refreshWorkflowChart");
                };

                // Determine whether or not we need to go out and GET this nodes unified job template
                // in order to determine whether or not prompt fields are needed

                if (!$scope.nodeBeingEdited.isNew && !$scope.nodeBeingEdited.edited && $scope.nodeBeingEdited.unifiedJobTemplate && $scope.nodeBeingEdited.unifiedJobTemplate.unified_job_type && $scope.nodeBeingEdited.unifiedJobTemplate.unified_job_type === 'job') {
                    // This is a node that we got back from the api with an incomplete
                    // unified job template so we're going to pull down the whole object

                    TemplatesService.getUnifiedJobTemplate($scope.nodeBeingEdited.unifiedJobTemplate.id)
                        .then(function(data) {
                            $scope.nodeBeingEdited.unifiedJobTemplate = _.clone(data.data.results[0]);
                            finishConfiguringEdit();
                        }, function(error) {
                            ProcessErrors($scope, error.data, error.status, form, {
                                hdr: 'Error!',
                                msg: 'Failed to get unified job template. GET returned ' +
                                    'status: ' + error.status
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

        $scope.startDeleteNode = function(nodeToDelete) {
            $scope.nodeToBeDeleted = nodeToDelete;
            $scope.deleteOverlayVisible = true;
        };

        $scope.cancelDeleteNode = function() {
            resetDeleteNode();
        };

        $scope.confirmDeleteNode = function() {
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

                // Reset the edgeConflict flag
                resetEdgeConflict();

                resetDeleteNode();

                $scope.$broadcast("refreshWorkflowChart");

                if($scope.placeholderNode) {
                    let edgeType = "success";
                    if($scope.placeholderNode.isRoot) {
                        edgeType = "always";
                    }
                    else {
                        // we need to update the possible edges based on any new siblings
                        let siblingConnectionTypes = WorkflowService.getSiblingConnectionTypes({
                            tree: $scope.treeData.data,
                            parentId: $scope.placeholderNode.parent.id,
                            childId: $scope.placeholderNode.id
                        });

                        if (_.includes(siblingConnectionTypes, "success") || _.includes(siblingConnectionTypes, "failure")) {
                            updateEdgeDropdownOptions(["success", "failure"]);
                        } else if (_.includes(siblingConnectionTypes, "always")) {
                            updateEdgeDropdownOptions(["always"]);
                            edgeType = "always";
                        } else {
                            updateEdgeDropdownOptions();
                        }

                    }
                    $scope.edgeType = edgeType;
                    // $scope.$broadcast("setEdgeType", edgeType);
                }
                else if($scope.nodeBeingEdited) {
                    let siblingConnectionTypes = WorkflowService.getSiblingConnectionTypes({
                        tree: $scope.treeData.data,
                        parentId: $scope.nodeBeingEdited.parent.id,
                        childId: $scope.nodeBeingEdited.id
                    });

                    if (_.includes(siblingConnectionTypes, "success") || _.includes(siblingConnectionTypes, "failure")) {
                        updateEdgeDropdownOptions(["success", "failure"]);
                    } else if (_.includes(siblingConnectionTypes, "always") && $scope.nodeBeingEdited.edgeType === "always") {
                        updateEdgeDropdownOptions(["always"]);
                    } else {
                        updateEdgeDropdownOptions();
                    }

                    switch($scope.nodeBeingEdited.edgeType) {
                       case "always":
                           $scope.edgeType = {label: "Always", value: "always"};
                           break;
                       case "success":
                           $scope.edgeType = {label: "On Success", value: "success"};
                           break;
                       case "failure":
                           $scope.edgeType = {label: "On Failure", value: "failure"};
                           break;
                   }
                }

                $scope.treeData.data.totalNodes--;
            }

        };

        $scope.toggleFormTab = function(tab) {
            if ($scope.workflowMakerFormConfig.activeTab !== tab) {
                $scope.workflowMakerFormConfig.activeTab = tab;
            }
        };

        $scope.templateManuallySelected = function(selectedTemplate) {

            $scope.selectedTemplate = angular.copy(selectedTemplate);

            if(selectedTemplate.type === "job_template") {
                let jobTemplate = new JobTemplate();

                $q.all([jobTemplate.optionsLaunch(selectedTemplate.id), jobTemplate.getLaunch(selectedTemplate.id)])
                    .then((responses) => {
                        let launchConf = responses[1].data;

                        if(!launchConf.survey_enabled &&
                            !launchConf.ask_inventory_on_launch &&
                            !launchConf.ask_credential_on_launch &&
                            !launchConf.ask_verbosity_on_launch &&
                            !launchConf.ask_job_type_on_launch &&
                            !launchConf.ask_limit_on_launch &&
                            !launchConf.ask_tags_on_launch &&
                            !launchConf.ask_skip_tags_on_launch &&
                            !launchConf.ask_diff_mode_on_launch &&
                            !launchConf.survey_enabled &&
                            !launchConf.credential_needed_to_start &&
                            !launchConf.inventory_needed_to_start &&
                            launchConf.passwords_needed_to_start.length === 0 &&
                            launchConf.variables_needed_to_start.length === 0) {
                                $scope.showPromptButton = false;
                        } else {
                            $scope.showPromptButton = true;

                            if(launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory')) {
                                $scope.promptModalMissingReqFields = true;
                            }

                            if(launchConf.survey_enabled) {
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

                                        $scope.$watch('promptData.surveyQuestions', () => {
                                            let missingSurveyValue = false;
                                            _.each($scope.promptData.surveyQuestions, (question) => {
                                                if(question.required && (Empty(question.model) || question.model === [])) {
                                                    missingSurveyValue = true;
                                                }
                                            });
                                            $scope.missingSurveyValue = missingSurveyValue;
                                        }, true);

                                        watchForPromptChanges();
                                    });
                            }
                            else {
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
                // TODO - clear out prompt data?
                $scope.showPromptButton = false;
            }
        };

        function resetEdgeConflict(){
            $scope.edgeFlags.conflict = false;

            WorkflowService.checkForEdgeConflicts({
                treeData: $scope.treeData.data,
                edgeFlags: $scope.edgeFlags
            });
        }

        $scope.toggleManualControls = function() {
            $scope.showManualControls = !$scope.showManualControls;
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

        $scope.workflowZoomed = function(zoom) {
            $scope.$broadcast('workflowZoomed', {
                zoom: zoom
            });
        };

        $scope.zoomToFitChart = function() {
            $scope.$broadcast('zoomToFitChart');
        };

        $scope.openPromptModal = function() {
            $scope.promptData.triggerModalOpen = true;
        };

        let allNodes = [];
        let page = 1;

        let buildTreeFromNodes = function(){
            WorkflowService.buildTree({
                workflowNodes: allNodes
            }).then(function(data){
                $scope.treeData = data;

                // TODO: I think that the workflow chart directive (and eventually d3) is meddling with
                // this treeData object and removing the children object for some reason (?)
                // This happens on occasion and I think is a race condition (?)
                if(!$scope.treeData.data.children) {
                    $scope.treeData.data.children = [];
                }

                $scope.treeData.workflow_job_template_obj = $scope.workflowJobTemplateObj;

                $scope.treeDataMaster = angular.copy($scope.treeData.data);
                $scope.showManualControls = false;
            });
        };

        let getNodes = function(){
            // Get the workflow nodes
            TemplatesService.getWorkflowJobTemplateNodes($scope.workflowJobTemplateObj.id, page)
            .then(function(data){
                for(var i=0; i<data.data.results.length; i++) {
                    allNodes.push(data.data.results[i]);
                }
                if(data.data.next) {
                    // Get the next page
                    page++;
                    getNodes();
                }
                else {
                    // This is the last page
                    buildTreeFromNodes();
                }
            }, function(error){
                ProcessErrors($scope, error.data, error.status, form, {
                    hdr: 'Error!',
                    msg: 'Failed to get workflow job template nodes. GET returned ' +
                    'status: ' + error.status
                });
            });
        };

        getNodes();

        updateEdgeDropdownOptions();

    }
];
