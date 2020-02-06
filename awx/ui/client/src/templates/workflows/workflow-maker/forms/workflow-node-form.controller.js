/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'TemplatesService', 'JobTemplateModel', 'PromptService', 'Rest', '$q',
        'TemplatesStrings', 'CreateSelect2', 'Empty', 'QuerySet', '$filter',
        'GetBasePath', 'WorkflowNodeFormService', 'ProcessErrors',
        'i18n', 'ParseTypeChange', 'WorkflowJobTemplateModel',
    function($scope, TemplatesService, JobTemplate, PromptService, Rest, $q,
        TemplatesStrings, CreateSelect2, Empty, qs, $filter,
        GetBasePath, WorkflowNodeFormService, ProcessErrors,
        i18n, ParseTypeChange, WorkflowJobTemplate
    ) {

        let promptWatcher, credentialsWatcher, surveyQuestionWatcher, listPromises = [];

        const shouldShowPromptButton = (launchConf) => launchConf.survey_enabled ||
            launchConf.ask_inventory_on_launch ||
            launchConf.ask_credential_on_launch ||
            launchConf.ask_verbosity_on_launch ||
            launchConf.ask_job_type_on_launch ||
            launchConf.ask_limit_on_launch ||
            launchConf.ask_tags_on_launch ||
            launchConf.ask_skip_tags_on_launch ||
            launchConf.ask_diff_mode_on_launch ||
            launchConf.credential_needed_to_start ||
            launchConf.ask_variables_on_launch ||
            launchConf.ask_scm_branch_on_launch ||
            launchConf.variables_needed_to_start.length !== 0;

        $scope.strings = TemplatesStrings;
        $scope.editNodeHelpMessage = null;

        $scope.templateList = WorkflowNodeFormService.templateListDefinition();
        $scope.inventorySourceList = WorkflowNodeFormService.inventorySourceListDefinition();
        $scope.projectList = WorkflowNodeFormService.projectListDefinition();

        const checkCredentialsForRequiredPasswords = () => {
            let credentialRequiresPassword = false;
            $scope.jobNodeState.promptData.prompts.credentials.value.forEach((credential) => {
                if ((credential.passwords_needed &&
                    credential.passwords_needed.length > 0) ||
                    (_.has(credential, 'inputs.vault_password') &&
                    credential.inputs.vault_password === "ASK")
                ) {
                    credentialRequiresPassword = true;
                }
            });

            $scope.jobNodeState.credentialRequiresPassword = credentialRequiresPassword;
        };

        const watchForPromptChanges = () => {
            let promptDataToWatch = [
                'jobNodeState.promptData.prompts.inventory.value',
                'jobNodeState.promptData.prompts.verbosity.value',
                'jobNodeState.missingSurveyValue'
            ];

            promptWatcher = $scope.$watchGroup(promptDataToWatch, () => {
                const templateType = _.get($scope, 'jobNodeState.promptData.templateType');
                let missingPromptValue = false;

                if ($scope.jobNodeState.missingSurveyValue) {
                    missingPromptValue = true;
                }

                if (templateType !== "workflow_job_template") {
                    if (!$scope.jobNodeState.promptData.prompts.inventory.value || !$scope.jobNodeState.promptData.prompts.inventory.value.id) {
                        missingPromptValue = true;
                    }
                }

                $scope.jobNodeState.promptModalMissingReqFields = missingPromptValue;
            });

            if ($scope.jobNodeState.promptData.launchConf.ask_credential_on_launch && $scope.jobNodeState.credentialRequiresPassword) {
                credentialsWatcher = $scope.$watch('jobNodeState.promptData.prompts.credentials', () => {
                    checkCredentialsForRequiredPasswords();
                });
            }
        };

        const clearWatchers = () => {
            if (promptWatcher) {
                promptWatcher();
            }

            if (surveyQuestionWatcher) {
                surveyQuestionWatcher();
            }

            if (credentialsWatcher) {
                credentialsWatcher();
            }
        };

        const select2ifyDropdowns = () => {
            CreateSelect2({
                element: '#workflow-node-types',
                multiple: false
            });
            CreateSelect2({
                element: '#workflow_node_edge',
                multiple: false
            });
            CreateSelect2({
                element: '#workflow_node_convergence',
                multiple: false
            });
        };

        const formatPopOverDetails = (model) => {
            const popOverDetails = {};
            popOverDetails.playbook = model.playbook || i18n._('NONE SELECTED');
            Object.keys(model.summary_fields).forEach(field => {
                if (field === 'project') {
                    popOverDetails.project = model.summary_fields[field].name || i18n._('NONE SELECTED');
                }
                if (field === 'inventory') {
                    popOverDetails.inventory = model.summary_fields[field].name || i18n._('NONE SELECTED');
                }
                if (field === 'credentials') {
                    if (model.summary_fields[field].length <= 0) {
                        popOverDetails.credentials = i18n._('NONE SELECTED');
                    }
                    else {
                        const credentialNames = model.summary_fields[field].map(({name}) => name);
                        popOverDetails.credentials = credentialNames.join('<br />');
                    }
                }
            });
            model.popOver = `
                <table>
                    <tr>
                        <td>${i18n._('INVENTORY')}&nbsp;</td>
                        <td>${$filter('sanitize')(popOverDetails.inventory)}</td>
                    </tr>
                    <tr>
                        <td>${i18n._('PROJECT')}&nbsp;</td>
                        <td>${$filter('sanitize')(popOverDetails.project)}</td>
                    </tr>
                    <tr>
                        <td>${i18n._('PLAYBOOK')}&nbsp;</td>
                        <td>${$filter('sanitize')(popOverDetails.playbook)}</td>
                    </tr>
                    <tr>
                        <td>${i18n._('CREDENTIAL')}&nbsp;</td>
                        <td>${$filter('sanitize')(popOverDetails.credentials)}</td>
                    </tr>
                </table>
            `;
        };

        const updateSelectedRow = () => {
            let unifiedJobTemplateId;
            switch($scope.activeTab) {
                case 'templates':
                    unifiedJobTemplateId = _.get($scope, 'jobNodeState.selectedTemplate.id') || null;
                    $scope.wf_maker_templates.forEach((row, i) => {
                        if (row.type === 'job_template') {
                            formatPopOverDetails(row);
                        }
                        $scope.wf_maker_templates[i].checked = (row.id === unifiedJobTemplateId) ? 1 : 0;
                    });
                    break;
                case 'project_syncs':
                    unifiedJobTemplateId = _.get($scope, 'projectNodeState.selectedTemplate.id') || null;
                    $scope.wf_maker_projects.forEach((row, i) => {
                        $scope.wf_maker_projects[i].checked = (row.id === unifiedJobTemplateId) ? 1 : 0;
                    });
                    break;
                case 'inventory_syncs':
                    unifiedJobTemplateId = _.get($scope, 'inventoryNodeState.selectedTemplate.id') || null;
                    $scope.wf_maker_inventory_sources.forEach((row, i) => {
                        $scope.wf_maker_inventory_sources[i].checked = (row.id === unifiedJobTemplateId) ? 1 : 0;
                    });
                    break;
            }
        };

        const getEditNodeHelpMessage = (selectedTemplate, workflowJobTemplateObj) => {
            if (selectedTemplate) {
                if (selectedTemplate.type === "workflow_job_template") {
                    if (workflowJobTemplateObj.inventory && selectedTemplate.ask_inventory_on_launch) {
                        return $scope.strings.get('workflow_maker.INVENTORY_WILL_OVERRIDE');
                    }

                    if (workflowJobTemplateObj.ask_inventory_on_launch && selectedTemplate.ask_inventory_on_launch) {
                        return $scope.strings.get('workflow_maker.INVENTORY_PROMPT_WILL_OVERRIDE');
                    }
                }

                if (selectedTemplate.type === "job_template") {
                    if (workflowJobTemplateObj.inventory) {
                        if (selectedTemplate.ask_inventory_on_launch) {
                            return $scope.strings.get('workflow_maker.INVENTORY_WILL_OVERRIDE');
                        }

                        return $scope.strings.get('workflow_maker.INVENTORY_WILL_NOT_OVERRIDE');
                    }

                    if (workflowJobTemplateObj.ask_inventory_on_launch) {
                        if (selectedTemplate.ask_inventory_on_launch) {
                            return $scope.strings.get('workflow_maker.INVENTORY_PROMPT_WILL_OVERRIDE');
                        }

                        return $scope.strings.get('workflow_maker.INVENTORY_PROMPT_WILL_NOT_OVERRIDE');
                    }
                }
            }

             return null;
        };

        const finishConfiguringEdit = () => {
            const ujt = _.get($scope, 'nodeConfig.node.fullUnifiedJobTemplateObject');
            const templateType = _.get(ujt, 'type');

            $scope.editNodeHelpMessage = getEditNodeHelpMessage(ujt, $scope.workflowJobTemplateObj);

            if (!$scope.readOnly) {
                let jobTemplate = templateType === "workflow_job_template" ? new WorkflowJobTemplate() : new JobTemplate();

                if (_.get($scope, 'nodeConfig.node.promptData') && !_.isEmpty($scope.nodeConfig.node.promptData)) {
                    $scope.jobNodeState.promptData = _.cloneDeep($scope.nodeConfig.node.promptData);
                    const launchConf = $scope.jobNodeState.promptData.launchConf;

                    if (!shouldShowPromptButton(launchConf)) {
                            $scope.jobNodeState.showPromptButton = false;
                            $scope.jobNodeState.promptModalMissingReqFields = false;
                    } else {
                        $scope.jobNodeState.showPromptButton = true;

                        if (templateType !== "workflow_job_template" && launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory') && !_.has($scope, 'nodeConfig.node.originalNodeObject.summary_fields.inventory')) {
                            $scope.jobNodeState.promptModalMissingReqFields = true;
                        } else {
                            $scope.jobNodeState.promptModalMissingReqFields = false;
                        }
                    }
                    watchForPromptChanges();
                    $scope.nodeFormDataLoaded = true;
                } else if (
                    _.get($scope, 'nodeConfig.node.fullUnifiedJobTemplateObject.unified_job_type') === 'job_template' ||
                    _.get($scope, 'nodeConfig.node.fullUnifiedJobTemplateObject.type') === 'job_template' ||
                    _.get($scope, 'nodeConfig.node.fullUnifiedJobTemplateObject.type') === 'workflow_job_template'
                ) {
                    let promises = [jobTemplate.optionsLaunch($scope.nodeConfig.node.fullUnifiedJobTemplateObject.id), jobTemplate.getLaunch($scope.nodeConfig.node.fullUnifiedJobTemplateObject.id)];

                    if (_.has($scope, 'nodeConfig.node.originalNodeObject.related.credentials')) {
                        Rest.setUrl($scope.nodeConfig.node.originalNodeObject.related.credentials);
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
                                currentValues: $scope.nodeConfig.node.originalNodeObject
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

                            if (
                                $scope.nodeConfig.node.fullUnifiedJobTemplateObject.type === "job_template" &&
                                ((!$scope.nodeConfig.node.fullUnifiedJobTemplateObject.inventory && !launchConf.ask_inventory_on_launch) ||
                                !$scope.nodeConfig.node.fullUnifiedJobTemplateObject.project)
                            ) {
                                $scope.jobNodeState.selectedTemplateInvalid = true;
                            } else {
                                $scope.jobNodeState.selectedTemplateInvalid = false;
                            }

                            let credentialRequiresPassword = false;

                            prompts.credentials.value.forEach((credential) => {
                                if(credential.inputs) {
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

                            $scope.jobNodeState.credentialRequiresPassword = credentialRequiresPassword;

                            if (!shouldShowPromptButton(launchConf)) {
                                    $scope.jobNodeState.showPromptButton = false;
                                    $scope.jobNodeState.promptModalMissingReqFields = false;
                                    $scope.nodeFormDataLoaded = true;
                            } else {
                                $scope.jobNodeState.showPromptButton = true;

                                if (launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory') && !_.has($scope, 'nodeConfig.node.originalNodeObject.summary_fields.inventory')) {
                                    $scope.jobNodeState.promptModalMissingReqFields = true;
                                } else {
                                    $scope.jobNodeState.promptModalMissingReqFields = false;
                                }

                                if (responses[1].data.survey_enabled) {
                                    // go out and get the survey questions
                                    jobTemplate.getSurveyQuestions($scope.nodeConfig.node.fullUnifiedJobTemplateObject.id)
                                        .then((surveyQuestionRes) => {

                                            let processed = PromptService.processSurveyQuestions({
                                                surveyQuestions: surveyQuestionRes.data.spec,
                                                extra_data: jsyaml.safeLoad(prompts.variables.value)
                                            });

                                            $scope.jobNodeState.missingSurveyValue = processed.missingSurveyValue;

                                            $scope.extraVars = (processed.extra_data === '' || _.isEmpty(processed.extra_data)) ? '---' : '---\n' + jsyaml.safeDump(processed.extra_data);

                                            // PromptService.processSurveyQuestions will strip the survey answers out of the extra
                                            // vars so we should update the prompt value
                                            prompts.variables = {
                                                value: $scope.extraVars
                                            };

                                            $scope.nodeConfig.node.promptData = $scope.jobNodeState.promptData = {
                                                launchConf: launchConf,
                                                launchOptions: launchOptions,
                                                prompts: prompts,
                                                surveyQuestions: surveyQuestionRes.data.spec,
                                                templateType: $scope.nodeConfig.node.fullUnifiedJobTemplateObject.type,
                                                template: $scope.nodeConfig.node.fullUnifiedJobTemplateObject.id
                                            };

                                            surveyQuestionWatcher = $scope.$watch('jobNodeState.promptData.surveyQuestions', () => {
                                                let missingSurveyValue = false;
                                                _.each($scope.jobNodeState.promptData.surveyQuestions, (question) => {
                                                    if (question.required && (Empty(question.model) || question.model === [])) {
                                                        missingSurveyValue = true;
                                                    }
                                                });
                                                $scope.jobNodeState.missingSurveyValue = missingSurveyValue;
                                            }, true);

                                            checkCredentialsForRequiredPasswords();

                                            watchForPromptChanges();

                                            $scope.nodeFormDataLoaded = true;
                                        });
                                } else {
                                    $scope.nodeConfig.node.promptData = $scope.jobNodeState.promptData = {
                                        launchConf: launchConf,
                                        launchOptions: launchOptions,
                                        prompts: prompts,
                                        templateType: $scope.nodeConfig.node.fullUnifiedJobTemplateObject.type,
                                        template: $scope.nodeConfig.node.fullUnifiedJobTemplateObject.id
                                    };

                                    checkCredentialsForRequiredPasswords();

                                    watchForPromptChanges();

                                    $scope.nodeFormDataLoaded = true;
                                }
                            }
                    });
                } else {
                    $scope.nodeFormDataLoaded = true;
                }

                if (_.get($scope, 'nodeConfig.node.fullUnifiedJobTemplateObject')) {
                    const selectedTemplate = $scope.nodeConfig.node.fullUnifiedJobTemplateObject;

                    if (selectedTemplate.unified_job_type) {
                        switch (selectedTemplate.unified_job_type) {
                            case "job":
                                $scope.activeTab = "templates";
                                $scope.jobNodeState.selectedTemplate = selectedTemplate;
                                break;
                            case "project_update":
                                $scope.activeTab = "project_syncs";
                                $scope.projectNodeState.selectedTemplate = selectedTemplate;
                                break;
                            case "inventory_update":
                                $scope.activeTab = "inventory_syncs";
                                $scope.inventoryNodeState.selectedTemplate = selectedTemplate;
                                break;
                        }
                    } else if (selectedTemplate.type) {
                        switch (selectedTemplate.type) {
                            case "job_template":
                            case "workflow_job_template":
                                $scope.activeTab = "templates";
                                $scope.jobNodeState.selectedTemplate = selectedTemplate;
                                break;
                            case "project":
                                $scope.activeTab = "project_syncs";
                                $scope.projectNodeState.selectedTemplate = selectedTemplate;
                                break;
                            case "inventory_source":
                                $scope.activeTab = "inventory_syncs";
                                $scope.inventoryNodeState.selectedTemplate = selectedTemplate;
                                break;
                        }
                    }
                    updateSelectedRow();
                } else {
                    $scope.activeTab = "templates";
                }

                select2ifyDropdowns();
            } else {
                $scope.jobTags = $scope.nodeConfig.node.originalNodeObject.job_tags ? $scope.nodeConfig.node.originalNodeObject.job_tags.split(',').map((tag) => (tag)) : [];
                $scope.skipTags = $scope.nodeConfig.node.originalNodeObject.skip_tags ? $scope.nodeConfig.node.originalNodeObject.skip_tags.split(',').map((tag) => (tag)) : [];
                $scope.showJobTags = true;
                $scope.showSkipTags = true;

                if (!$.isEmptyObject($scope.nodeConfig.node.originalNodeObject.extra_data)) {
                    $scope.extraVars = '---\n' + jsyaml.safeDump($scope.nodeConfig.node.originalNodeObject.extra_data);
                    $scope.showExtraVars = true;
                    $scope.parseType = 'yaml';

                    ParseTypeChange({
                        scope: $scope,
                        variable: 'extraVars',
                        field_id: 'workflow_node_form_extra_vars',
                        readOnly: true
                    });
                } else {
                    $scope.extraVars = null;
                    $scope.showExtraVars = false;
                }

                $scope.nodeFormDataLoaded = true;
            }

        };

        const setupNodeForm = () => {
            $scope.jobNodeState = {
                credentialRequiresPassword: false,
                missingSurveyValue: false,
                promptData: null,
                promptModalMissingReqFields: false,
                searchTags: [],
                selectedTemplate: null,
                selectedTemplateInvalid: false,
                showPromptButton: false
            };
            $scope.projectNodeState = {
                searchTags: [],
                selectedTemplate: null
            };
            $scope.inventoryNodeState = {
                searchTags: [],
                selectedTemplate: null,
            };
            $scope.approvalNodeState = {
                name: null,
                description: null,
                timeoutMinutes: 0,
                timeoutSeconds: 0
            };
            $scope.nodeFormDataLoaded = false;
            $scope.wf_maker_template_queryset = {
                page_size: '10',
                order_by: 'name',
                role_level: 'execute_role',
                type: 'workflow_job_template,job_template'
            };

            const all_parents_must_converge = _.get(
                $scope, ['nodeConfig', 'node', 'all_parents_must_converge'],
                _.get($scope, ['nodeConfig', 'node', 'originalNodeObject', 'all_parents_must_converge'], false)
            );
            $scope.convergenceOptions = [
                {
                    label: $scope.strings.get('workflow_maker.ALL'),
                    value: true,
                },
                {
                    label: $scope.strings.get('workflow_maker.ANY'),
                    value: false,
                },
            ];
            $scope.convergenceChoice = $scope.convergenceOptions.find(({ value }) => value === all_parents_must_converge);

            $scope.wf_maker_templates = [];
            $scope.wf_maker_template_dataset = {};

            // Go out and GET the list contents for each of the tabs

            listPromises.push(
                qs.search(GetBasePath('unified_job_templates'), $scope.wf_maker_template_queryset)
                .then((res) => {
                    $scope.wf_maker_template_dataset = res.data;
                    $scope.wf_maker_templates = $scope.wf_maker_template_dataset.results;
                })
            );

            $scope.wf_maker_project_queryset = {
                page_size: '10',
                order_by: 'name'
            };

            $scope.wf_maker_projects = [];
            $scope.wf_maker_project_dataset = {};

            listPromises.push(
                qs.search(GetBasePath('projects'), $scope.wf_maker_project_queryset)
                .then((res) => {
                    $scope.wf_maker_project_dataset = res.data;
                    $scope.wf_maker_projects = $scope.wf_maker_project_dataset.results;
                })
            );

            $scope.wf_maker_inventory_source_dataset = {
                page_size: '10',
                order_by: 'name',
                not__source: ''
            };

            $scope.wf_maker_inventory_sources = [];
            $scope.wf_maker_inventory_source_dataset = {};

            listPromises.push(
                qs.search(GetBasePath('inventory_sources'), $scope.wf_maker_inventory_source_dataset)
                .then((res) => {
                    $scope.wf_maker_inventory_source_dataset = res.data;
                    $scope.wf_maker_inventory_sources = $scope.wf_maker_inventory_source_dataset.results;
                })
            );

            $q.all(listPromises)
                .then(() => {
                    if ($scope.nodeConfig.mode === "edit") {
                        if ($scope.nodeConfig.node.unifiedJobTemplate && $scope.nodeConfig.node.unifiedJobTemplate.unified_job_type === "workflow_approval") {
                            $scope.activeTab = "approval";
                            select2ifyDropdowns();

                            const timeoutMinutes = Math.floor($scope.nodeConfig.node.unifiedJobTemplate.timeout / 60);
                            const timeoutSeconds = $scope.nodeConfig.node.unifiedJobTemplate.timeout - timeoutMinutes * 60;

                            $scope.approvalNodeState = {
                                name: $scope.nodeConfig.node.unifiedJobTemplate.name,
                                description: $scope.nodeConfig.node.unifiedJobTemplate.description,
                                timeoutMinutes,
                                timeoutSeconds
                            };

                            $scope.nodeFormDataLoaded = true;
                        } else {
                            // Make sure that we have the full unified job template object
                            if (!$scope.nodeConfig.node.fullUnifiedJobTemplateObject && _.has($scope, 'nodeConfig.node.originalNodeObject.summary_fields.unified_job_template')) {
                                // This is a node that we got back from the api with an incomplete
                                // unified job template so we're going to pull down the whole object
                                TemplatesService.getUnifiedJobTemplate($scope.nodeConfig.node.originalNodeObject.summary_fields.unified_job_template.id)
                                    .then(({data}) => {
                                        $scope.nodeConfig.node.fullUnifiedJobTemplateObject = data.results[0];
                                        finishConfiguringEdit();
                                    }, (error) => {
                                        ProcessErrors($scope, error.data, error.status, null, {
                                            hdr: 'Error!',
                                            msg: 'Failed to get unified job template. GET returned ' +
                                                'status: ' + error.status
                                        });
                                    });
                            } else {
                                finishConfiguringEdit();
                            }
                        }
                    } else {
                        $scope.activeTab = "templates";
                        const alwaysOption = {
                            label: $scope.strings.get('workflow_maker.ALWAYS'),
                            value: 'always'
                        };
                        const successOption = {
                            label: $scope.strings.get('workflow_maker.ON_SUCCESS'),
                            value: 'success'
                        };
                        const failureOption = {
                            label: $scope.strings.get('workflow_maker.ON_FAILURE'),
                            value: 'failure'
                        };
                        $scope.edgeTypeOptions = [alwaysOption];
                        switch($scope.nodeConfig.newNodeIsRoot) {
                            case true:
                                $scope.edgeType = alwaysOption;
                                break;
                            case false:
                                $scope.edgeType = successOption;
                                $scope.edgeTypeOptions.push(successOption, failureOption);
                                break;
                        }
                        select2ifyDropdowns();

                        $scope.nodeFormDataLoaded = true;
                    }
                });
        };

        $scope.confirmNodeForm = () => {
            const nodeFormData = {
                edgeType: $scope.edgeType,
                all_parents_must_converge: $scope.convergenceChoice.value,
            };

            if ($scope.activeTab === "approval") {
                const timeout = $scope.approvalNodeState.timeoutMinutes * 60 + $scope.approvalNodeState.timeoutSeconds;

                nodeFormData.selectedTemplate = {
                    name: $scope.approvalNodeState.name,
                    description: $scope.approvalNodeState.description,
                    timeout,
                    unified_job_type: "workflow_approval"
                };
            } else if($scope.activeTab === "templates") {
                nodeFormData.selectedTemplate = $scope.jobNodeState.selectedTemplate;
                nodeFormData.promptData = $scope.jobNodeState.promptData;
            } else if($scope.activeTab === "project_syncs") {
                nodeFormData.selectedTemplate = $scope.projectNodeState.selectedTemplate;
            } else if($scope.activeTab === "inventory_syncs") {
                nodeFormData.selectedTemplate = $scope.inventoryNodeState.selectedTemplate;
            }

            $scope.select({ nodeFormData });
        };

        $scope.openPromptModal = () => {
            $scope.jobNodeState.promptData.triggerModalOpen = true;
        };

        $scope.selectIsDisabled = () => {
            if($scope.activeTab === "templates") {
                return !($scope.jobNodeState.selectedTemplate) ||
                    $scope.jobNodeState.promptModalMissingReqFields ||
                    $scope.jobNodeState.credentialRequiresPassword ||
                    $scope.jobNodeState.selectedTemplateInvalid;
            } else if($scope.activeTab === "project_syncs") {
                return !$scope.projectNodeState.selectedTemplate;
            } else if($scope.activeTab === "inventory_syncs") {
                return !$scope.inventoryNodeState.selectedTemplate;
            } else if ($scope.activeTab === "approval") {
                return !($scope.approvalNodeState.name && $scope.approvalNodeState.name !== "") || $scope.workflow_approval.pauseTimeoutMinutes.$error.min || $scope.workflow_approval.pauseTimeoutSeconds.$error.min;
            }
        };

        $scope.selectTemplate = (selectedTemplate) => {
            if (!$scope.readOnly) {
                clearWatchers();

                $scope.approvalNodeState = {
                    name: null,
                    description: null,
                    timeoutMinutes: 0,
                    timeoutSeconds: 0
                };
                $scope.editNodeHelpMessage = getEditNodeHelpMessage(selectedTemplate, $scope.workflowJobTemplateObj);

                if (selectedTemplate.type === "job_template" || selectedTemplate.type === "workflow_job_template") {
                    let jobTemplate = selectedTemplate.type === "workflow_job_template" ? new WorkflowJobTemplate() : new JobTemplate();
                    $scope.jobNodeState.promptData = null;

                    $q.all([jobTemplate.optionsLaunch(selectedTemplate.id), jobTemplate.getLaunch(selectedTemplate.id)])
                        .then((responses) => {
                            let launchConf = responses[1].data;

                            let credentialRequiresPassword = false;
                            let selectedTemplateInvalid = false;

                            if (selectedTemplate.type !== "workflow_job_template") {
                                if ((!selectedTemplate.inventory && !launchConf.ask_inventory_on_launch) || !selectedTemplate.project) {
                                    selectedTemplateInvalid = true;
                                }

                                if (launchConf.passwords_needed_to_start && launchConf.passwords_needed_to_start.length > 0) {
                                    credentialRequiresPassword = true;
                                }
                            }

                            $scope.jobNodeState.credentialRequiresPassword = credentialRequiresPassword;
                            $scope.jobNodeState.selectedTemplateInvalid = selectedTemplateInvalid;
                            $scope.jobNodeState.selectedTemplate = angular.copy(selectedTemplate);
                            updateSelectedRow();

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
                                    $scope.jobNodeState.showPromptButton = false;
                                    $scope.jobNodeState.promptModalMissingReqFields = false;
                            } else {
                                $scope.jobNodeState.showPromptButton = true;
                                $scope.jobNodeState.promptModalMissingReqFields = false;

                                if (selectedTemplate.type !== "workflow_job_template") {
                                    if (launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory')) {
                                        $scope.jobNodeState.promptModalMissingReqFields = true;
                                    }
                                }

                                if (launchConf.survey_enabled) {
                                    // go out and get the survey questions
                                    jobTemplate.getSurveyQuestions(selectedTemplate.id)
                                        .then((surveyQuestionRes) => {

                                            let processed = PromptService.processSurveyQuestions({
                                                surveyQuestions: surveyQuestionRes.data.spec
                                            });

                                            $scope.jobNodeState.missingSurveyValue = processed.missingSurveyValue;

                                            $scope.jobNodeState.promptData = {
                                                launchConf: responses[1].data,
                                                launchOptions: responses[0].data,
                                                surveyQuestions: processed.surveyQuestions,
                                                template: selectedTemplate.id,
                                                templateType: selectedTemplate.type,
                                                prompts: PromptService.processPromptValues({
                                                    launchConf: responses[1].data,
                                                    launchOptions: responses[0].data
                                                }),
                                            };

                                            surveyQuestionWatcher = $scope.$watch('jobNodeState.promptData.surveyQuestions', () => {
                                                let missingSurveyValue = false;
                                                _.each($scope.jobNodeState.promptData.surveyQuestions, (question) => {
                                                    if (question.required && (Empty(question.model) || question.model === [])) {
                                                        missingSurveyValue = true;
                                                    }
                                                });
                                                $scope.jobNodeState.missingSurveyValue = missingSurveyValue;
                                            }, true);

                                            watchForPromptChanges();
                                        });
                                } else {
                                    $scope.jobNodeState.promptData = {
                                        launchConf: responses[1].data,
                                        launchOptions: responses[0].data,
                                        template: selectedTemplate.id,
                                        templateType: selectedTemplate.type,
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
                    if (selectedTemplate.type === "project") {
                        $scope.projectNodeState.selectedTemplate = angular.copy(selectedTemplate);
                    } else if (selectedTemplate.type === "inventory_source") {
                        $scope.inventoryNodeState.selectedTemplate = angular.copy(selectedTemplate);
                    }
                    updateSelectedRow();
                }
            }
        };

        $scope.$watch('nodeConfig.nodeId', (newNodeId, oldNodeId) => {
            if (newNodeId !== oldNodeId) {
                clearWatchers();
                setupNodeForm();
            }
        });

        $scope.$watchGroup(['wf_maker_templates', 'wf_maker_projects', 'wf_maker_inventory_sources', 'activeTab'], () => {
            updateSelectedRow();
        });

        setupNodeForm();
    }
];
