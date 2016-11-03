/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
 [   '$scope', '$stateParams', 'WorkflowForm', 'GenerateForm', 'Alert', 'ProcessErrors',
     'ClearScope', 'GetBasePath', '$q', 'ParseTypeChange', 'Wait', 'Empty',
     'ToJSON', 'initSurvey', '$state', 'CreateSelect2', 'ParseVariableString',
     'JobTemplateService', 'OrganizationList', 'Rest',
     function(
         $scope, $stateParams, WorkflowForm, GenerateForm, Alert, ProcessErrors,
         ClearScope, GetBasePath, $q, ParseTypeChange, Wait, Empty,
         ToJSON, SurveyControllerInit, $state, CreateSelect2, ParseVariableString,
         JobTemplateService, OrganizationList, Rest
     ) {

        ClearScope();

        $scope.$watch('workflow_job_template_obj.summary_fields.user_capabilities.edit', function(val) {
            if (val === false) {
                $scope.canAdd = false;
            }
        });

        // Inject dynamic view
        let form = WorkflowForm(),
            generator = GenerateForm,
            id = $stateParams.workflow_job_template_id;

        $scope.mode = 'edit';
        $scope.parseType = 'yaml';
        $scope.includeWorkflowMaker = false;

        // What is this used for?  Permissions?
        $scope.can_edit = true;

        $scope.editRequests = [];
        $scope.associateRequests = [];
        $scope.disassociateRequests = [];

        $scope.workflowTree = {
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
                id: $scope.workflowTree.nextIndex,
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

            $scope.workflowTree.data.totalNodes++;

            $scope.workflowTree.nextIndex++;

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

        function init() {
            // // Inject the edit form
            // generator.inject(form, {
            //     mode: 'edit' ,
            //     scope: $scope,
            //     related: false
            // });
            // generator.reset();

            // Select2-ify the lables input
            CreateSelect2({
                element:'#workflow_job_template_labels',
                multiple: true,
                addNew: true
            });

            // // Make the variables textarea look nice
            // ParseTypeChange({
            //     scope: $scope,
            //     field_id: 'workflow_job_template_variables',
            //     onChange: function() {
            //         $scope[form.name + '_form'].$setDirty();
            //     }
            // });

            // // Initialize the organization lookup
            // LookUpInit({
            //     scope: $scope,
            //     form: form,
            //     list: OrganizationList,
            //     field: 'organization',
            //     input_type: 'radio'
            // });

            Rest.setUrl('api/v1/labels');
            Wait("start");
            Rest.get()
                .success(function (data) {
                    $scope.labelOptions = data.results
                        .map((i) => ({label: i.name, value: i.id}));

                    var seeMoreResolve = $q.defer();

                    var getNext = function(data, arr, resolve) {
                        Rest.setUrl(data.next);
                        Rest.get()
                            .success(function (data) {
                                if (data.next) {
                                    getNext(data, arr.concat(data.results), resolve);
                                } else {
                                    resolve.resolve(arr.concat(data.results));
                                }
                            });
                    };

                    Rest.setUrl(GetBasePath('workflow_job_templates') + id +
                         "/labels");
                    Rest.get()
                        .success(function(data) {
                            if (data.next) {
                                getNext(data, data.results, seeMoreResolve);
                            } else {
                                seeMoreResolve.resolve(data.results);
                            }

                            seeMoreResolve.promise.then(function (labels) {
                                $scope.$emit("choicesReady");
                                var opts = labels
                                    .map(i => ({id: i.id + "",
                                        test: i.name}));
                                CreateSelect2({
                                    element:'#workflow_job_template_labels',
                                    multiple: true,
                                    addNew: true,
                                    opts: opts
                                });
                                Wait("stop");
                            });
                        }).error(function(){
                            // job template id is null in this case
                            $scope.$emit("choicesReady");
                        });

                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to get labels. GET returned ' +
                            'status: ' + status
                    });
                });

            // Get the workflow nodes
            JobTemplateService.getWorkflowJobTemplateNodes(id)
            .then(function(data){

                let nodesArray = data.data.results;
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

                    $scope.workflowTree.data.children.push(branch);
                });

                // TODO: I think that the workflow chart directive (and eventually d3) is meddling with
                // this workflowTree object and removing the children object for some reason (?)
                // This happens on occasion and I think is a race condition (?)
                if(!$scope.workflowTree.data.children) {
                    $scope.workflowTree.data.children = [];
                }

                // In the partial, the workflow maker directive has an ng-if attribute which is pointed at this scope variable.
                // It won't get included until this the tree has been built - I'm open to better ways of doing this.
                $scope.includeWorkflowMaker = true;

            }, function(error){
                ProcessErrors($scope, error.data, error.status, form, {
                    hdr: 'Error!',
                    msg: 'Failed to get workflow job template nodes. GET returned ' +
                    'status: ' + error.status
                });
            });

            // Go out and GET the workflow job temlate data needed to populate the form
            JobTemplateService.getWorkflowJobTemplate(id)
            .then(function(data){
                let workflowJobTemplateData = data.data;
                $scope.workflow_job_template_obj = workflowJobTemplateData;
                $scope.name = workflowJobTemplateData.name;
                let fld, i;
                for (fld in form.fields) {
                    if (fld !== 'variables' && fld !== 'survey' && workflowJobTemplateData[fld] !== null && workflowJobTemplateData[fld] !== undefined) {
                        if (form.fields[fld].type === 'select') {
                            if ($scope[fld + '_options'] && $scope[fld + '_options'].length > 0) {
                                for (i = 0; i < $scope[fld + '_options'].length; i++) {
                                    if (workflowJobTemplateData[fld] === $scope[fld + '_options'][i].value) {
                                        $scope[fld] = $scope[fld + '_options'][i];
                                    }
                                }
                            } else {
                                $scope[fld] = workflowJobTemplateData[fld];
                            }
                        } else {
                            $scope[fld] = workflowJobTemplateData[fld];
                            if(!Empty(workflowJobTemplateData.summary_fields.survey)) {
                                $scope.survey_exists = true;
                            }
                        }
                    }
                    if (fld === 'variables') {
                        // Parse extra_vars, converting to YAML.
                        $scope.variables = ParseVariableString(workflowJobTemplateData.extra_vars);

                        ParseTypeChange({ scope: $scope, field_id: 'workflow_job_template_variables' });
                    }
                    if (form.fields[fld].type === 'lookup' && workflowJobTemplateData.summary_fields[form.fields[fld].sourceModel]) {
                        $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                        workflowJobTemplateData.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                    }
                }
                Wait('stop');
                $scope.url = workflowJobTemplateData.url;
                $scope.survey_enabled = workflowJobTemplateData.survey_enabled;

            }, function(error){
                ProcessErrors($scope, error.data, error.status, form, {
                    hdr: 'Error!',
                    msg: 'Failed to get workflow job template. GET returned ' +
                'status: ' + error.status
                });
            });
        }

        function recursiveNodeUpdates(params, completionCallback) {
            // params.parentId
            // params.node

            let generatePostUrl = function(){

                let base = (params.parentId) ? GetBasePath('workflow_job_template_nodes') + params.parentId : $scope.workflow_job_template_obj.related.workflow_nodes;

                if(params.parentId) {
                    if(params.node.edgeType === 'success') {
                        base += "/success_nodes";
                    }
                    else if(params.node.edgeType === 'failure') {
                        base += "/failure_nodes";
                    }
                    else if(params.node.edgeType === 'always') {
                        base += "/always_nodes";
                    }
                }

                return base;

            };

            let buildSendableNodeData = function() {
                // Create the node
                let sendableNodeData = {
                    unified_job_template: params.node.unifiedJobTemplate.id
                };

                // Check to see if the user has provided any prompt values that are different
                // from the defaults in the job template

                if(params.node.unifiedJobTemplate.type === "job_template" && params.node.promptValues) {
                    if(params.node.unifiedJobTemplate.ask_credential_on_launch) {
                        sendableNodeData.credential = !params.node.promptValues.credential || params.node.unifiedJobTemplate.summary_fields.credential.id !== params.node.promptValues.credential.id ? params.node.promptValues.credential.id : null;
                    }
                    if(params.node.unifiedJobTemplate.ask_inventory_on_launch) {
                        sendableNodeData.inventory = !params.node.promptValues.inventory || params.node.unifiedJobTemplate.summary_fields.inventory.id !== params.node.promptValues.inventory.id ? params.node.promptValues.inventory.id : null;
                    }
                    if(params.node.unifiedJobTemplate.ask_limit_on_launch) {
                        sendableNodeData.limit =  !params.node.promptValues.limit || params.node.unifiedJobTemplate.limit !== params.node.promptValues.limit ? params.node.promptValues.limit : null;
                    }
                    if(params.node.unifiedJobTemplate.ask_job_type_on_launch) {
                        sendableNodeData.job_type =  !params.node.promptValues.job_type || params.node.unifiedJobTemplate.job_type !== params.node.promptValues.job_type ? params.node.promptValues.job_type : null;
                    }
                    if(params.node.unifiedJobTemplate.ask_tags_on_launch) {
                        sendableNodeData.job_tags =  !params.node.promptValues.job_tags || params.node.unifiedJobTemplate.job_tags !== params.node.promptValues.job_tags ? params.node.promptValues.job_tags : null;
                    }
                    if(params.node.unifiedJobTemplate.ask_skip_tags_on_launch) {
                        sendableNodeData.skip_tags =  !params.node.promptValues.skip_tags || params.node.unifiedJobTemplate.skip_tags !== params.node.promptValues.skip_tags ? params.node.promptValues.skip_tags : null;
                    }
                }

                return sendableNodeData;
            };

            let continueRecursing = function(parentId) {
                $scope.totalIteratedNodes++;

                if($scope.totalIteratedNodes === $scope.workflowTree.data.totalNodes) {
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

                JobTemplateService.addWorkflowNode({
                    url: generatePostUrl(),
                    data: buildSendableNodeData()
                })
                .then(function(data) {
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

                        $scope.editRequests.push({
                            id: params.node.nodeId,
                            data: buildSendableNodeData()
                        });

                    }

                    if((params.node.originalParentId && params.parentId !== params.node.originalParentId) || params.node.originalEdge !== params.node.edgeType) {//beep

                        $scope.disassociateRequests.push({
                            parentId: params.node.originalParentId,
                            nodeId: params.node.nodeId,
                            edge: params.node.originalEdge
                        });

                        // Can only associate if we have a parent.
                        // If we don't have a parent then this is a root node
                        // and the act of disassociating will make it a root node
                        if(params.parentId) {
                            $scope.associateRequests.push({
                                parentId: params.parentId,
                                nodeId: params.node.nodeId,
                                edge: params.node.edgeType
                            });
                        }

                    }
                    else if(!params.node.originalParentId && params.parentId) {
                        // This used to be a root node but is now not a root node
                        $scope.associateRequests.push({
                            parentId: params.parentId,
                            nodeId: params.node.nodeId,
                            edge: params.node.edgeType
                        });
                    }

                }

            continueRecursing(params.node.nodeId);
        }
    }

    $scope.openWorkflowMaker = function() {
        $state.go('.workflowMaker');
    };

    $scope.formSave = function () {
        let fld, data = {};
        $scope.invalid_survey = false;

        // Can't have a survey enabled without a survey
        if($scope.survey_enabled === true && $scope.survey_exists!==true){
            $scope.survey_enabled = false;
        }

        generator.clearApiErrors($scope);

        Wait('start');

        try {
            for (fld in form.fields) {
                data[fld] = $scope[fld];
            }

            data.extra_vars = ToJSON($scope.parseType,
                $scope.variables, true);

                // The idea here is that we want to find the new option elements that also have a label that exists in the dom
                $("#workflow_job_template_labels > option").filter("[data-select2-tag=true]").each(function(optionIndex, option) {
                    $("#workflow_job_template_labels").siblings(".select2").first().find(".select2-selection__choice").each(function(labelIndex, label) {
                        if($(option).text() === $(label).attr('title')) {
                            // Mark that the option has a label present so that we can filter by that down below
                            $(option).attr('data-label-is-present', true);
                        }
                    });
                });

                $scope.newLabels = $("#workflow_job_template_labels > option")
                .filter("[data-select2-tag=true]")
                .filter("[data-label-is-present=true]")
                .map((i, val) => ({name: $(val).text()}));

                $scope.totalIteratedNodes = 0;

                // TODO: this is the only way that I could figure out to get
                // these promise arrays to play nicely.  I tried to just append
                // a single promise to deletePromises but it just wasn't working
                let editWorkflowJobTemplate = [id].map(function(id) {
                    return JobTemplateService.updateWorkflowJobTemplate({
                        id: id,
                        data: data
                    });
                });

                if($scope.workflowTree && $scope.workflowTree.data && $scope.workflowTree.data.children && $scope.workflowTree.data.children.length > 0) {
                    let completionCallback = function() {

                        let disassociatePromises = $scope.disassociateRequests.map(function(request) {
                            return JobTemplateService.disassociateWorkflowNode({
                                parentId: request.parentId,
                                nodeId: request.nodeId,
                                edge: request.edge
                            });
                        });

                        let editNodePromises = $scope.editRequests.map(function(request) {
                            return JobTemplateService.editWorkflowNode({
                                id: request.id,
                                data: request.data
                            });
                        });

                        $q.all(disassociatePromises.concat(editNodePromises).concat(editWorkflowJobTemplate))
                        .then(function() {

                            let associatePromises = $scope.associateRequests.map(function(request) {
                                return JobTemplateService.associateWorkflowNode({
                                    parentId: request.parentId,
                                    nodeId: request.nodeId,
                                    edge: request.edge
                                });
                            });

                            let deletePromises = $scope.workflowTree.data.deletedNodes.map(function(nodeId) {
                                return JobTemplateService.deleteWorkflowJobTemplateNode(nodeId);
                            });

                            $q.all(associatePromises.concat(deletePromises))
                            .then(function() {

                                var orgDefer = $q.defer();
                                var associationDefer = $q.defer();
                                var associatedLabelsDefer = $q.defer();

                                var getNext = function(data, arr, resolve) {
                                    Rest.setUrl(data.next);
                                    Rest.get()
                                        .success(function (data) {
                                            if (data.next) {
                                                getNext(data, arr.concat(data.results), resolve);
                                            } else {
                                                resolve.resolve(arr.concat(data.results));
                                            }
                                        });
                                };

                                Rest.setUrl($scope.workflow_job_template_obj.related.labels);

                                Rest.get()
                                    .success(function(data) {
                                        if (data.next) {
                                            getNext(data, data.results, associatedLabelsDefer);
                                        } else {
                                            associatedLabelsDefer.resolve(data.results);
                                        }
                                    });

                                associatedLabelsDefer.promise.then(function (current) {
                                    current = current.map(data => data.id);
                                    var labelsToAdd = $scope.labels
                                        .map(val => val.value);
                                    var labelsToDisassociate = current
                                        .filter(val => labelsToAdd
                                            .indexOf(val) === -1)
                                        .map(val => ({id: val, disassociate: true}));
                                    var labelsToAssociate = labelsToAdd
                                        .filter(val => current
                                            .indexOf(val) === -1)
                                        .map(val => ({id: val, associate: true}));
                                    var pass = labelsToDisassociate
                                        .concat(labelsToAssociate);
                                    associationDefer.resolve(pass);
                                });

                                Rest.setUrl(GetBasePath("organizations"));
                                Rest.get()
                                    .success(function(data) {
                                        orgDefer.resolve(data.results[0].id);
                                    });

                                orgDefer.promise.then(function(orgId) {
                                    var toPost = [];
                                    $scope.newLabels = $scope.newLabels
                                        .map(function(i, val) {
                                            val.organization = orgId;
                                            return val;
                                        });

                                    $scope.newLabels.each(function(i, val) {
                                        toPost.push(val);
                                    });

                                    associationDefer.promise.then(function(arr) {
                                        toPost = toPost
                                            .concat(arr);

                                        Rest.setUrl($scope.workflow_job_template_obj.related.labels);

                                        var defers = [];
                                        for (var i = 0; i < toPost.length; i++) {
                                            defers.push(Rest.post(toPost[i]));
                                        }
                                        $q.all(defers)
                                            .then(function() {
                                                $state.go('templates.editWorkflowJobTemplate', {id: id}, {reload: true});
                                            });
                                    });
                                });

                            });
                        });
                    };

                    _.forEach($scope.workflowTree.data.children, function(child) {
                        recursiveNodeUpdates({
                            node: child
                        }, completionCallback);
                    });
                }
                else {

                    let deletePromises = $scope.workflowTree.data.deletedNodes.map(function(nodeId) {
                        return JobTemplateService.deleteWorkflowJobTemplateNode(nodeId);
                    });

                    $q.all(deletePromises.concat(editWorkflowJobTemplate))
                    .then(function() {
                        var orgDefer = $q.defer();
                        var associationDefer = $q.defer();
                        var associatedLabelsDefer = $q.defer();

                        var getNext = function(data, arr, resolve) {
                            Rest.setUrl(data.next);
                            Rest.get()
                                .success(function (data) {
                                    if (data.next) {
                                        getNext(data, arr.concat(data.results), resolve);
                                    } else {
                                        resolve.resolve(arr.concat(data.results));
                                    }
                                });
                        };

                        Rest.setUrl($scope.workflow_job_template_obj.related.labels);

                        Rest.get()
                            .success(function(data) {
                                if (data.next) {
                                    getNext(data, data.results, associatedLabelsDefer);
                                } else {
                                    associatedLabelsDefer.resolve(data.results);
                                }
                            });

                        associatedLabelsDefer.promise.then(function (current) {
                            current = current.map(data => data.id);
                            var labelsToAdd = $scope.labels
                                .map(val => val.value);
                            var labelsToDisassociate = current
                                .filter(val => labelsToAdd
                                    .indexOf(val) === -1)
                                .map(val => ({id: val, disassociate: true}));
                            var labelsToAssociate = labelsToAdd
                                .filter(val => current
                                    .indexOf(val) === -1)
                                .map(val => ({id: val, associate: true}));
                            var pass = labelsToDisassociate
                                .concat(labelsToAssociate);
                            associationDefer.resolve(pass);
                        });

                        Rest.setUrl(GetBasePath("organizations"));
                        Rest.get()
                            .success(function(data) {
                                orgDefer.resolve(data.results[0].id);
                            });

                        orgDefer.promise.then(function(orgId) {
                            var toPost = [];
                            $scope.newLabels = $scope.newLabels
                                .map(function(i, val) {
                                    val.organization = orgId;
                                    return val;
                                });

                            $scope.newLabels.each(function(i, val) {
                                toPost.push(val);
                            });

                            associationDefer.promise.then(function(arr) {
                                toPost = toPost
                                    .concat(arr);

                                Rest.setUrl($scope.workflow_job_template_obj.related.labels);

                                var defers = [];
                                for (var i = 0; i < toPost.length; i++) {
                                    defers.push(Rest.post(toPost[i]));
                                }
                                $q.all(defers)
                                    .then(function() {
                                        $state.go('templates.editWorkflowJobTemplate', {id: id}, {reload: true});
                                    });
                            });
                        });
                        //$state.go('templates.editWorkflowJobTemplate', {id: id}, {reload: true});
                    });
                }

            } catch (err) {
                Wait('stop');
                Alert("Error", "Error saving workflow job template. " +
                "Parser returned: " + err);
            }
        };

        $scope.formCancel = function () {
            $state.transitionTo('templates');
        };

        init();
    }
];
