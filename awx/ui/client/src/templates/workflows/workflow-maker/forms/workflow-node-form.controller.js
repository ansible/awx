/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'TemplatesService', 'JobTemplateModel', 'PromptService', 'Rest', '$q',
        'TemplatesStrings', 'CreateSelect2', 'Empty', 'generateList', 'QuerySet',
        'GetBasePath', 'TemplateList', 'ProjectList', 'InventorySourcesList', 'ProcessErrors',
        'i18n', 'ParseTypeChange', 'WorkflowJobTemplateModel',
    function($scope, TemplatesService, JobTemplate, PromptService, Rest, $q,
        TemplatesStrings, CreateSelect2, Empty, generateList, qs,
        GetBasePath, TemplateList, ProjectList, InventorySourcesList, ProcessErrors,
        i18n, ParseTypeChange, WorkflowJobTemplate
    ) {

        let promptWatcher, credentialsWatcher, surveyQuestionWatcher, listPromises = [];

        $scope.strings = TemplatesStrings;
        $scope.editNodeHelpMessage = null;

        let templateList = _.cloneDeep(TemplateList);
        delete templateList.actions;
        delete templateList.fields.type;
        delete templateList.fields.description;
        delete templateList.fields.smart_status;
        delete templateList.fields.labels;
        delete templateList.fieldActions;
        templateList.name = 'wf_maker_templates';
        templateList.iterator = 'wf_maker_template';
        templateList.fields.name.columnClass = "col-md-8";
        templateList.fields.name.tag = i18n._('WORKFLOW');
        templateList.fields.name.showTag = "{{wf_maker_template.type === 'workflow_job_template'}}";
        templateList.disableRow = "{{ readOnly }}";
        templateList.disableRowValue = 'readOnly';
        templateList.basePath = 'unified_job_templates';
        templateList.fields.info = {
            ngInclude: "'/static/partials/job-template-details.html'",
            type: 'template',
            columnClass: 'col-md-3',
            infoHeaderClass: 'col-md-3',
            label: '',
            nosort: true
        };
        templateList.maxVisiblePages = 5;
        templateList.searchBarFullWidth = true;
        $scope.templateList = templateList;

        let inventorySourceList = _.cloneDeep(InventorySourcesList);
        inventorySourceList.name = 'wf_maker_inventory_sources';
        inventorySourceList.iterator = 'wf_maker_inventory_source';
        inventorySourceList.maxVisiblePages = 5;
        inventorySourceList.searchBarFullWidth = true;
        inventorySourceList.disableRow = "{{ readOnly }}";
        inventorySourceList.disableRowValue = 'readOnly';
        $scope.inventorySourceList = inventorySourceList;

        let projectList = _.cloneDeep(ProjectList);
        delete projectList.fields.status;
        delete projectList.fields.scm_type;
        delete projectList.fields.last_updated;
        projectList.name = 'wf_maker_projects';
        projectList.iterator = 'wf_maker_project';
        projectList.fields.name.columnClass = "col-md-11";
        projectList.maxVisiblePages = 5;
        projectList.searchBarFullWidth = true;
        projectList.disableRow = "{{ readOnly }}";
        projectList.disableRowValue = 'readOnly';
        $scope.projectList = projectList;

        const checkCredentialsForRequiredPasswords = () => {
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

        const watchForPromptChanges = () => {
            let promptDataToWatch = [
                'promptData.prompts.inventory.value',
                'promptData.prompts.verbosity.value',
                'missingSurveyValue'
            ];

            promptWatcher = $scope.$watchGroup(promptDataToWatch, () => {
                const templateType = _.get($scope, 'promptData.templateType');
                let missingPromptValue = false;

                if ($scope.missingSurveyValue) {
                    missingPromptValue = true;
                }

                if (templateType !== "workflow_job_template") {
                    if (!$scope.promptData.prompts.inventory.value || !$scope.promptData.prompts.inventory.value.id) {
                        missingPromptValue = true;
                    }
                }

                $scope.promptModalMissingReqFields = missingPromptValue;
            });

            if ($scope.promptData.launchConf.ask_credential_on_launch && $scope.credentialRequiresPassword) {
                credentialsWatcher = $scope.$watch('promptData.prompts.credentials', () => {
                    checkCredentialsForRequiredPasswords();
                });
            }
        };

        const finishConfiguringAdd = () => {
            $scope.selectedTemplate = null;
            $scope.activeTab = "jobs";
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
            CreateSelect2({
                element: '#workflow_node_edge',
                multiple: false
            });

            $scope.nodeFormDataLoaded = true;
        };

        const getEditNodeHelpMessage = (selectedTemplate, workflowJobTemplateObj) => {
            if (selectedTemplate) {
                if (selectedTemplate.type === "workflow_job_template") {
                    if (workflowJobTemplateObj.inventory) {
                        if (selectedTemplate.ask_inventory_on_launch) {
                            return $scope.strings.get('workflow_maker.INVENTORY_WILL_OVERRIDE');
                        }
                    }

                    if (workflowJobTemplateObj.ask_inventory_on_launch) {
                        if (selectedTemplate.ask_inventory_on_launch) {
                            return $scope.strings.get('workflow_maker.INVENTORY_PROMPT_WILL_OVERRIDE');
                        }
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
                    $scope.promptData = _.cloneDeep($scope.nodeConfig.node.promptData);
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

                        if (templateType !== "workflow_job_template" && launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory') && !_.has($scope, 'nodeConfig.node.originalNodeObject.summary_fields.inventory')) {
                            $scope.promptModalMissingReqFields = true;
                        } else {
                            $scope.promptModalMissingReqFields = false;
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
                                $scope.selectedTemplateInvalid = true;
                            } else {
                                $scope.selectedTemplateInvalid = false;
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
                                    $scope.nodeFormDataLoaded = true;
                            } else {
                                $scope.showPromptButton = true;

                                if (launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory') && !_.has($scope, 'nodeConfig.node.originalNodeObject.summary_fields.inventory')) {
                                    $scope.promptModalMissingReqFields = true;
                                } else {
                                    $scope.promptModalMissingReqFields = false;
                                }

                                if (responses[1].data.survey_enabled) {
                                    // go out and get the survey questions
                                    jobTemplate.getSurveyQuestions($scope.nodeConfig.node.fullUnifiedJobTemplateObject.id)
                                        .then((surveyQuestionRes) => {

                                            let processed = PromptService.processSurveyQuestions({
                                                surveyQuestions: surveyQuestionRes.data.spec,
                                                extra_data: _.cloneDeep($scope.nodeConfig.node.originalNodeObject.extra_data)
                                            });

                                            $scope.missingSurveyValue = processed.missingSurveyValue;

                                            $scope.extraVars = (processed.extra_data === '' || _.isEmpty(processed.extra_data)) ? '---' : '---\n' + jsyaml.safeDump(processed.extra_data);

                                            $scope.nodeConfig.node.promptData = $scope.promptData = {
                                                launchConf: launchConf,
                                                launchOptions: launchOptions,
                                                prompts: prompts,
                                                surveyQuestions: surveyQuestionRes.data.spec,
                                                templateType: $scope.nodeConfig.node.fullUnifiedJobTemplateObject.type,
                                                template: $scope.nodeConfig.node.fullUnifiedJobTemplateObject.id
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

                                            $scope.nodeFormDataLoaded = true;
                                        });
                                } else {
                                    $scope.nodeConfig.node.promptData = $scope.promptData = {
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
                    $scope.selectedTemplate = $scope.nodeConfig.node.fullUnifiedJobTemplateObject;

                    if ($scope.selectedTemplate.unified_job_type) {
                        switch ($scope.selectedTemplate.unified_job_type) {
                            case "job":
                                $scope.activeTab = "jobs";
                                break;
                            case "project_update":
                                $scope.activeTab = "project_syncs";
                                break;
                            case "inventory_update":
                                $scope.activeTab = "inventory_syncs";
                                break;
                        }
                    } else if ($scope.selectedTemplate.type) {
                        switch ($scope.selectedTemplate.type) {
                            case "job_template":
                                $scope.activeTab = "jobs";
                                break;
                            case "workflow_job_template":
                                $scope.activeTab = "jobs";
                                break;
                            case "project":
                                $scope.activeTab = "project_syncs";
                                break;
                            case "inventory_source":
                                $scope.activeTab = "inventory_syncs";
                                break;
                        }
                    }
                } else {
                    $scope.activeTab = "jobs";
                }
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

        const templateManuallySelected = (selectedTemplate) => {

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
            $scope.editNodeHelpMessage = getEditNodeHelpMessage(selectedTemplate, $scope.workflowJobTemplateObj);

            if (selectedTemplate.type === "job_template" || selectedTemplate.type === "workflow_job_template") {
                let jobTemplate = selectedTemplate.type === "workflow_job_template" ? new WorkflowJobTemplate() : new JobTemplate();

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

                        $scope.credentialRequiresPassword = credentialRequiresPassword;
                        $scope.selectedTemplateInvalid = selectedTemplateInvalid;
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
                            $scope.promptModalMissingReqFields = false;

                            if (selectedTemplate.type !== "workflow_job_template") {
                                if (launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory')) {
                                    $scope.promptModalMissingReqFields = true;
                                }
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
                                            templateType: selectedTemplate.type,
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
                $scope.selectedTemplate = angular.copy(selectedTemplate);
                $scope.selectedTemplateInvalid = false;
                $scope.showPromptButton = false;
                $scope.promptModalMissingReqFields = false;
            }
        };

        const setupNodeForm = () => {
            $scope.nodeFormDataLoaded = false;
            $scope.wf_maker_template_queryset = {
                page_size: '10',
                order_by: 'name',
                role_level: 'execute_role',
                type: 'workflow_job_template,job_template'
            };

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
                        // Make sure that we have the full unified job template object
                        if (!$scope.nodeConfig.node.fullUnifiedJobTemplateObject) {
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
                    } else {
                        finishConfiguringAdd();
                    }
                });
        };

        const formatPopOverDetails = (model) => {
            model.popOverDetails = {};
            model.popOverDetails.playbook = model.playbook || i18n._('NONE SELECTED');
            Object.keys(model.summary_fields).forEach(field => {
                if (field === 'project') {
                    model.popOverDetails.project = model.summary_fields[field].name || i18n._('NONE SELECTED');
                }
                if (field === 'inventory') {
                    model.popOverDetails.inventory = model.summary_fields[field].name || i18n._('NONE SELECTED');
                }
                if (field === 'credentials') {
                    if (model.summary_fields[field].length <= 0) {
                        model.popOverDetails.credentials = i18n._('NONE SELECTED');
                    }
                    else {
                        const credentialNames = model.summary_fields[field].map(({name}) => name);
                        model.popOverDetails.credentials = credentialNames.join('<br />');
                    }
                }
            });
        };

        $scope.openPromptModal = () => {
            $scope.promptData.triggerModalOpen = true;
        };

        $scope.toggle_row = (selectedRow) => {
            if (!$scope.readOnly) {
                templateManuallySelected(selectedRow);
            }
        };

        $scope.$watch('nodeConfig.nodeId', (newNodeId, oldNodeId) => {
            if (newNodeId !== oldNodeId) {
                setupNodeForm();
            }
        });

        $scope.$watchGroup(['wf_maker_templates', 'wf_maker_projects', 'wf_maker_inventory_sources', 'activeTab', 'selectedTemplate.id'], () => {
            const unifiedJobTemplateId = _.get($scope, 'selectedTemplate.id') || null;
            switch($scope.activeTab) {
                case 'jobs':
                    $scope.wf_maker_templates.forEach((row, i) => {
                        if (row.type === 'job_template') {
                            formatPopOverDetails(row);
                        }
                        if(row.id === unifiedJobTemplateId) {
                            $scope.wf_maker_templates[i].checked = 1;
                        }
                        else {
                            $scope.wf_maker_templates[i].checked = 0;
                        }
                    });
                    break;
                case 'project_syncs':
                    $scope.wf_maker_projects.forEach((row, i) => {
                        if(row.id === unifiedJobTemplateId) {
                            $scope.wf_maker_projects[i].checked = 1;
                        }
                        else {
                            $scope.wf_maker_projects[i].checked = 0;
                        }
                    });
                    break;
                case 'inventory_syncs':
                    $scope.wf_maker_inventory_sources.forEach((row, i) => {
                        if(row.id === unifiedJobTemplateId) {
                            $scope.wf_maker_inventory_sources[i].checked = 1;
                        }
                        else {
                            $scope.wf_maker_inventory_sources[i].checked = 0;
                        }
                    });
                    break;
            }
        });

        setupNodeForm();
    }
];
