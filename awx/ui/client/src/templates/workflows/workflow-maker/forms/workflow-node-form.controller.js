/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'TemplatesService', 'JobTemplateModel', 'PromptService', 'Rest', '$q',
        'WorkflowService', 'TemplatesStrings', 'CreateSelect2', 'Empty', 'generateList', 'QuerySet',
        'GetBasePath', 'TemplateList', 'ProjectList', 'InventorySourcesList',
    function($scope, TemplatesService, JobTemplate, PromptService, Rest, $q,
        WorkflowService, TemplatesStrings, CreateSelect2, Empty, generateList, qs,
        GetBasePath, TemplateList, ProjectList, InventorySourcesList
    ) {

        let promptWatcher, credentialsWatcher, surveyQuestionWatcher, listPromises = [];

        $scope.strings = TemplatesStrings;

        let templateList = _.cloneDeep(TemplateList);
        delete templateList.actions;
        delete templateList.fields.type;
        delete templateList.fields.description;
        delete templateList.fields.smart_status;
        delete templateList.fields.labels;
        delete templateList.fieldActions;
        templateList.fields.name.columnClass = "col-md-8";
        templateList.disableRow = "{{ readOnly }}";
        templateList.disableRowValue = 'readOnly';
        templateList.fields.info = {
            ngInclude: "'/static/partials/job-template-details.html'",
            type: 'template',
            columnClass: 'col-md-3',
            label: '',
            nosort: true
        };
        templateList.maxVisiblePages = 5;
        templateList.searchBarFullWidth = true;
        $scope.templateList = templateList;

        let inventorySourceList = _.cloneDeep(InventorySourcesList);
        inventorySourceList.maxVisiblePages = 5;
        inventorySourceList.searchBarFullWidth = true;
        inventorySourceList.disableRow = "{{ readOnly }}";
        inventorySourceList.disableRowValue = 'readOnly';
        $scope.inventorySourceList = inventorySourceList;

        let projectList = _.cloneDeep(ProjectList);
        delete projectList.fields.status;
        delete projectList.fields.scm_type;
        delete projectList.fields.last_updated;
        projectList.fields.name.columnClass = "col-md-11";
        projectList.maxVisiblePages = 5;
        projectList.searchBarFullWidth = true;
        projectList.disableRow = "{{ readOnly }}";
        projectList.disableRowValue = 'readOnly';
        $scope.projectList = projectList;

        $scope.$watch('node', (newNode, oldNode) => {
            if (oldNode.id !== newNode.id) {
                setupNodeForm();
            }
        });

        $scope.$watchGroup(['templates', 'projects', 'inventory_sources', 'activeTab'], () => {
            // TODO: make this more concise
            switch($scope.activeTab) {
                case 'jobs':
                    $scope.templates.forEach(function(row, i) {
                        if(_.hasIn($scope, 'node.unifiedJobTemplate.id') && row.id === $scope.node.unifiedJobTemplate.id) {
                            $scope.templates[i].checked = 1;
                        }
                        else {
                            $scope.templates[i].checked = 0;
                        }
                    });
                    break;
                case 'project_syncs':
                    $scope.projects.forEach(function(row, i) {
                        if(_.hasIn($scope, 'node.unifiedJobTemplate.id') && row.id === $scope.node.unifiedJobTemplate.id) {
                            $scope.projects[i].checked = 1;
                        }
                        else {
                            $scope.projects[i].checked = 0;
                        }
                    });
                    break;
                case 'inventory_syncs':
                    $scope.inventory_sources.forEach(function(row, i) {
                        if(_.hasIn($scope, 'node.unifiedJobTemplate.id') && row.id === $scope.node.unifiedJobTemplate.id) {
                            $scope.inventory_sources[i].checked = 1;
                        }
                        else {
                            $scope.inventory_sources[i].checked = 0;
                        }
                    });
                    break;
            }
        });

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

            promptWatcher = $scope.$watchGroup(promptDataToWatch, function() {
                let missingPromptValue = false;
                if ($scope.missingSurveyValue) {
                    missingPromptValue = true;
                } else if (!$scope.promptData.prompts.inventory.value || !$scope.promptData.prompts.inventory.value.id) {
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

        const finishConfiguringEdit = () => {

            let jobTemplate = new JobTemplate();

            console.log($scope.node);

            if (!_.isEmpty($scope.node.promptData)) {
                $scope.promptData = _.cloneDeep($scope.node.promptData);
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

                    if (launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory') && !_.has($scope, 'node.originalNodeObj.summary_fields.inventory')) {
                        $scope.promptModalMissingReqFields = true;
                    } else {
                        $scope.promptModalMissingReqFields = false;
                    }
                }
                $scope.nodeFormDataLoaded = true;
            } else if (
                _.get($scope, 'node.unifiedJobTemplate.unified_job_type') === 'job_template' ||
                _.get($scope, 'node.unifiedJobTemplate.type') === 'job_template'
            ) {
                let promises = [jobTemplate.optionsLaunch($scope.node.unifiedJobTemplate.id), jobTemplate.getLaunch($scope.node.unifiedJobTemplate.id)];

                if (_.has($scope, 'node.originalNodeObj.related.credentials')) {
                    Rest.setUrl($scope.node.originalNodeObj.related.credentials);
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
                            currentValues: $scope.node.originalNodeObj
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

                        if ((!$scope.node.unifiedJobTemplate.inventory && !launchConf.ask_inventory_on_launch) || !$scope.node.unifiedJobTemplate.project) {
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

                            if (launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory') && !_.has($scope, 'node.originalNodeObj.summary_fields.inventory')) {
                                $scope.promptModalMissingReqFields = true;
                            } else {
                                $scope.promptModalMissingReqFields = false;
                            }

                            if (responses[1].data.survey_enabled) {
                                // go out and get the survey questions
                                jobTemplate.getSurveyQuestions($scope.node.unifiedJobTemplate.id)
                                    .then((surveyQuestionRes) => {

                                        let processed = PromptService.processSurveyQuestions({
                                            surveyQuestions: surveyQuestionRes.data.spec,
                                            extra_data: _.cloneDeep($scope.node.originalNodeObj.extra_data)
                                        });

                                        $scope.missingSurveyValue = processed.missingSurveyValue;

                                        $scope.extraVars = (processed.extra_data === '' || _.isEmpty(processed.extra_data)) ? '---' : '---\n' + jsyaml.safeDump(processed.extra_data);

                                        $scope.node.promptData = $scope.promptData = {
                                            launchConf: launchConf,
                                            launchOptions: launchOptions,
                                            prompts: prompts,
                                            surveyQuestions: surveyQuestionRes.data.spec,
                                            template: $scope.node.unifiedJobTemplate.id
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
                                $scope.node.promptData = $scope.promptData = {
                                    launchConf: launchConf,
                                    launchOptions: launchOptions,
                                    prompts: prompts,
                                    template: $scope.node.unifiedJobTemplate.id
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

            if (_.get($scope, 'node.unifiedJobTemplate')) {
                if (_.get($scope, 'node.unifiedJobTemplate.type') === "job_template") {
                    $scope.activeTab = "jobs";
                }

                $scope.selectedTemplate = $scope.node.unifiedJobTemplate;

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

            if ($scope.mode === 'add') {
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
                switch($scope.node.isRoot) {
                    case true:
                        $scope.edgeType = alwaysOption;
                        break;
                    case false:
                        $scope.edgeType = successOption;
                        $scope.edgeTypeOptions.push(successOption, failureOption);
                        break;
                }
                CreateSelect2({
                    element: '#workflow_node_edge_3',
                    multiple: false
                });

                $scope.nodeFormDataLoaded = true;
            }
        };
        // Determine whether or not we need to go out and GET this nodes unified job template
        // in order to determine whether or not prompt fields are needed

        $scope.openPromptModal = function() {
            $scope.promptData.triggerModalOpen = true;
        };

        $scope.toggle_row = function(selectedRow) {
            if (!$scope.readOnly) {
                // TODO: make this more concise
                switch($scope.activeTab) {
                    case 'jobs':
                        $scope.templates.forEach(function(row, i) {
                            if (row.id === selectedRow.id) {
                                $scope.templates[i].checked = 1;

                            } else {
                                $scope.templates[i].checked = 0;
                            }
                        });
                        break;
                    case 'project_syncs':
                        $scope.projects.forEach(function(row, i) {
                            if (row.id === selectedRow.id) {
                                $scope.projects[i].checked = 1;
                            } else {
                                $scope.projects[i].checked = 0;
                            }
                        });
                        break;
                    case 'inventory_syncs':
                        $scope.inventory_sources.forEach(function(row, i) {
                            if (row.id === selectedRow.id) {
                                $scope.inventory_sources[i].checked = 1;
                            } else {
                                $scope.inventory_sources[i].checked = 0;
                            }
                        });
                        break;
                }
                templateManuallySelected(selectedRow);
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

            if (selectedTemplate.type === "job_template") {
                let jobTemplate = new JobTemplate();

                $q.all([jobTemplate.optionsLaunch(selectedTemplate.id), jobTemplate.getLaunch(selectedTemplate.id)])
                    .then((responses) => {
                        let launchConf = responses[1].data;

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

                            if (launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory')) {
                                $scope.promptModalMissingReqFields = true;
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

        const setupNodeForm = () => {
            $scope.nodeFormDataLoaded = false;
            $scope.template_queryset = {
                page_size: '5',
                order_by: 'name',
                type: 'workflow_job_template,job_template'
            };

            $scope.templates = [];
            $scope.template_dataset = {};

            // Go out and GET the list contents for each of the tabs

            listPromises.push(
                qs.search(GetBasePath('unified_job_templates'), $scope.template_queryset)
                .then(function(res) {
                    $scope.template_dataset = res.data;
                    $scope.templates = $scope.template_dataset.results;
                })
            );

            $scope.project_queryset = {
                page_size: '5',
                order_by: 'name'
            };

            $scope.projects = [];
            $scope.project_dataset = {};

            listPromises.push(
                qs.search(GetBasePath('projects'), $scope.project_queryset)
                .then(function(res) {
                    $scope.project_dataset = res.data;
                    $scope.projects = $scope.project_dataset.results;
                })
            );

            $scope.inventory_source_dataset = {
                page_size: '5',
                order_by: 'name',
                not__source: ''
            }

            $scope.inventory_sources = [];
            $scope.inventory_source_dataset = {};

            listPromises.push(
                qs.search(GetBasePath('inventory_sources'), $scope.inventory_source_dataset)
                .then(function(res) {
                    $scope.inventory_source_dataset = res.data;
                    $scope.inventory_sources = $scope.inventory_source_dataset.results;
                })
            );

            $q.all(listPromises)
                .then(() => {
                    if (!$scope.node.isNew && !$scope.node.edited && $scope.node.unifiedJobTemplate && $scope.node.unifiedJobTemplate.unified_job_type && $scope.node.unifiedJobTemplate.unified_job_type === 'job') {
                        // This is a node that we got back from the api with an incomplete
                        // unified job template so we're going to pull down the whole object

                        TemplatesService.getUnifiedJobTemplate($scope.node.unifiedJobTemplate.id)
                            .then(function(data) {
                                $scope.node.unifiedJobTemplate = _.clone(data.data.results[0]);
                                finishConfiguringEdit();
                            }, function(error) {
                                ProcessErrors($scope, error.data, error.status, null, {
                                    hdr: 'Error!',
                                    msg: 'Failed to get unified job template. GET returned ' +
                                        'status: ' + error.status
                                });
                            });
                    } else {
                        finishConfiguringEdit();
                    }
                });
        }

        setupNodeForm();
    }
];
