function ListTemplatesController (model, JobTemplate, WorkflowJobTemplate, strings, $state, $scope, rbacUiControlService, Dataset, $filter, Alert, InitiatePlaybookRun, Prompt, Wait, ProcessErrors, TemplateCopyService, $q, Empty, i18n, PromptService) {
    const vm = this || {},
          unifiedJobTemplate = model,
          jobTemplate = new JobTemplate(),
          workflowJobTemplate = new WorkflowJobTemplate();

    vm.strings = strings;

    // TODO: add the permission based functionality to the base model
    $scope.canAdd = false;
    rbacUiControlService.canAdd("job_templates")
    .then(function(params) {
        $scope.canAddJobTemplate = params.canAdd;
    });
    rbacUiControlService.canAdd("workflow_job_templates")
        .then(function(params) {
            $scope.canAddWorkflowJobTemplate = params.canAdd;
        });
    $scope.$watchGroup(["canAddJobTemplate", "canAddWorkflowJobTemplate"], function() {
        if ($scope.canAddJobTemplate || $scope.canAddWorkflowJobTemplate) {
            $scope.canAdd = true;
        } else {
            $scope.canAdd = false;
        }
    });

    $scope.list = {
        iterator: 'template',
        name: 'templates'
    };
    $scope.collection = {
        basePath: 'unified_job_templates',
        iterator: 'template'
    };
    $scope[`${$scope.list.iterator}_dataset`] = Dataset.data;
    $scope[$scope.list.name] = $scope[`${$scope.list.iterator}_dataset`].results;
    $scope.$on('updateDataset', function(e, dataset) {
        $scope[`${$scope.list.iterator}_dataset`] = dataset;
        $scope[$scope.list.name] = dataset.results;
    });

    // get modified date and user who modified it
    vm.getModified = function(template) {
        let val = "";
        if (template.modified) {
            val += $filter('longDate')(template.modified);
        }
        if (_.has(template, 'summary_fields.modified_by.username')) {
                val += ` by <a href="/#/users/${template.summary_fields.modified_by.id}">${template.summary_fields.modified_by.username}</a>`;
        }
        if (val === "") {
            val = undefined;
        }
        return val;
    };

    // get last ran date and user who ran it
    vm.getRan = function(template) {
        let val = "";
        if (template.last_job_run) {
            val += $filter('longDate')(template.last_job_run);
        }

        // TODO: when API gives back a user who last ran the job in summary fields, uncomment and
        // update this code
        // if (template && template.summary_fields && template.summary_fields.modified_by &&
        //     template.summary_fields.modified_by.username) {
        //         val += ` by <a href="/#/users/${template.summary_fields.modified_by.id}">${template.summary_fields.modified_by.username}</a>`;
        // }

        if (val === "") {
            val = undefined;
        }
        return val;
    };

    // get pretified template type names from options
    vm.templateTypes = unifiedJobTemplate.options('actions.GET.type.choices')
        .reduce((acc, i) => {
            acc[i[0]] = i[1];
            return acc;
        }, {});

    // get if you should show the active indicator for the row or not
    // TODO: edit indicator doesn't update when you enter edit route after initial load right now
    vm.activeId = parseInt($state.params.job_template_id || $state.params.workflow_template_id);

    vm.submitJob = function(template) {
        if(template) {
            if(template.type && (template.type === 'Job Template' || template.type === 'job_template')) {
                let jobTemplate = new JobTemplate();

                $q.all([jobTemplate.optionsLaunch(template.id), jobTemplate.getLaunch(template.id)])
                    .then((responses) => {
                        if(jobTemplate.canLaunchWithoutPrompt()) {
                            jobTemplate.postLaunch({id: template.id})
                                .then((launchRes) => {
                                    $state.go('jobResult', { id: launchRes.data.job }, { reload: true });
                                });
                        } else {

                            if(responses[1].data.survey_enabled) {

                                // go out and get the survey questions
                                jobTemplate.getSurveyQuestions(template.id)
                                    .then((surveyQuestionRes) => {

                                        let processed = PromptService.processSurveyQuestions({
                                            surveyQuestions: surveyQuestionRes.data.spec
                                        });
                                        
                                        $scope.promptData = {
                                            launchConf: responses[1].data,
                                            launchOptions: responses[0].data,
                                            surveyQuestions: processed.surveyQuestions,
                                            template: template.id,
                                            prompts: PromptService.processPromptValues({
                                                launchConf: responses[1].data,
                                                launchOptions: responses[0].data
                                            }),
                                            triggerModalOpen: true
                                        };
                                    });
                            }
                            else {
                                $scope.promptData = {
                                    launchConf: responses[1].data,
                                    launchOptions: responses[0].data,
                                    template: template.id,
                                    prompts: PromptService.processPromptValues({
                                        launchConf: responses[1].data,
                                        launchOptions: responses[0].data
                                    }),
                                    triggerModalOpen: true
                                };
                            }
                        }
                    });
            }
            else if(template.type && (template.type === 'Workflow Job Template' || template.type === 'workflow_job_template')) {
                InitiatePlaybookRun({ scope: $scope, id: template.id, job_type: 'workflow_job_template' });
            }
            else {
                // Something went wrong - Let the user know that we're unable to launch because we don't know
                // what type of job template this is
                Alert('Error: Unable to determine template type', 'We were unable to determine this template\'s type while launching.');
            }
        }
        else {
            Alert('Error: Unable to launch template', 'Template parameter is missing');
        }
    };

    $scope.launchJob = () => {

        let jobLaunchData = {
            extra_vars: $scope.promptData.extraVars
        };

        let jobTemplate = new JobTemplate();

        if($scope.promptData.launchConf.ask_tags_on_launch){
            jobLaunchData.job_tags = $scope.promptData.prompts.tags.value.map(a => a.value).join();
        }
        if($scope.promptData.launchConf.ask_skip_tags_on_launch){
            jobLaunchData.skip_tags = $scope.promptData.prompts.skipTags.value.map(a => a.value).join();
        }
        if($scope.promptData.launchConf.ask_limit_on_launch && _.has($scope, 'promptData.prompts.limit.value')){
            jobLaunchData.limit = $scope.promptData.prompts.limit.value;
        }
        if($scope.promptData.launchConf.ask_job_type_on_launch && _.has($scope, 'promptData.prompts.jobType.value.value')) {
            jobLaunchData.job_type = $scope.promptData.prompts.jobType.value.value;
        }
        if($scope.promptData.launchConf.ask_verbosity_on_launch && _.has($scope, 'promptData.prompts.verbosity.value.value')) {
            jobLaunchData.verbosity = $scope.promptData.prompts.verbosity.value.value;
        }
        if($scope.promptData.launchConf.ask_inventory_on_launch && !Empty($scope.promptData.prompts.inventory.value.id)){
            jobLaunchData.inventory_id = $scope.promptData.prompts.inventory.value.id;
        }
        if($scope.promptData.launchConf.ask_credential_on_launch){
            jobLaunchData.credentials = [];
            $scope.promptData.prompts.credentials.value.forEach((credential) => {
                jobLaunchData.credentials.push(credential.id);
            });
        }
        if($scope.promptData.launchConf.ask_diff_mode_on_launch && _.has($scope, 'promptData.prompts.diffMode.value')) {
            jobLaunchData.diff_mode = $scope.promptData.prompts.diffMode.value;
        }

        if($scope.promptData.prompts.credentials.passwords) {
            _.forOwn($scope.promptData.prompts.credentials.passwords, (val, key) => {
                if(!jobLaunchData.credential_passwords) {
                    jobLaunchData.credential_passwords = {};
                }
                if(key === "ssh_key_unlock") {
                    jobLaunchData.credential_passwords.ssh_key_unlock = val.value;
                } else if(key !== "vault") {
                    jobLaunchData.credential_passwords[`${key}_password`] = val.value;
                } else {
                    _.each(val, (vaultCred) => {
                        jobLaunchData.credential_passwords[vaultCred.vault_id ? `${key}_password.${vaultCred.vault_id}` : `${key}_password`] = vaultCred.value;
                    });
                }
            });
        }

        // If the extra_vars dict is empty, we don't want to include it if we didn't prompt for anything.
        if(_.isEmpty(jobLaunchData.extra_vars) && !($scope.promptData.launchConf.ask_variables_on_launch && $scope.promptData.launchConf.survey_enabled && $scope.promptData.surveyQuestions.length > 0)){
            delete jobLaunchData.extra_vars;
        }

        jobTemplate.postLaunch({
            id: $scope.promptData.template,
            launchData: jobLaunchData
        }).then((launchRes) => {
            $state.go('jobResult', { id: launchRes.data.job }, { reload: true });
        }).catch(({data, status}) => {
            ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'),
            msg: i18n.sprintf(i18n._('Failed to launch job template. POST returned: %d'), $scope.promptData.template, status) });
        });
    };

    vm.scheduleJob = (template) => {
        if(template) {
            if(template.type && (template.type === 'Job Template' || template.type === 'job_template')) {
                $state.go('jobTemplateSchedules', {id: template.id});
            }
            else if(template.type && (template.type === 'Workflow Job Template' || template.type === 'workflow_job_template')) {
                $state.go('workflowJobTemplateSchedules', {id: template.id});
            }
            else {
                // Something went wrong  Let the user know that we're unable to redirect to schedule because we don't know
                // what type of job template this is
                Alert('Error: Unable to determine template type', 'We were unable to determine this template\'s type while routing to schedule.');
            }
        }
        else {
            Alert('Error: Unable to schedule job', 'Template parameter is missing');
        }
    };

    vm.scheduleJob = (template) => {
        if(template) {
            if(template.type && (template.type === 'Job Template' || template.type === 'job_template')) {
                $state.go('jobTemplateSchedules', {id: template.id});
            }
            else if(template.type && (template.type === 'Workflow Job Template' || template.type === 'workflow_job_template')) {
                $state.go('workflowJobTemplateSchedules', {id: template.id});
            }
            else {
                // Something went wrong  Let the user know that we're unable to redirect to schedule because we don't know
                // what type of job template this is
                Alert('Error: Unable to determine template type', 'We were unable to determine this template\'s type while routing to schedule.');
            }
        }
        else {
            Alert('Error: Unable to schedule job', 'Template parameter is missing');
        }
    };

    vm.copyTemplate = function(template) {

        if(template) {
            if(template.type && template.type === 'job_template') {
                Wait('start');
                TemplateCopyService.get(template.id)
                 .then(function(response){
                        TemplateCopyService.set(response.data.results)
                        .then(function(results){
                            Wait('stop');
                            if(results.type && results.type === 'job_template') {
                                $state.go('templates.editJobTemplate', {job_template_id: results.id}, {reload: true});
                            }
                        })
                        .catch(({data, status}) => {
                            ProcessErrors($scope, data, status, null, {
                                hdr: 'Error!',
                                msg: 'Call failed. Return status: ' + status
                            });
                        });
                    })
                .catch(({data, status}) => {
                    ProcessErrors($scope, data, status, null, {hdr: 'Error!',
                    msg: 'Call failed. Return status: '+ status});
                });
            }
            else if(template.type && template.type === 'workflow_job_template') {
                TemplateCopyService.getWorkflowCopy(template.id)
                .then(function(result) {

                    if(result.data.can_copy) {
                        if(result.data.can_copy_without_user_input) {
                            // Go ahead and copy the workflow - the user has full priveleges on all the resources
                            TemplateCopyService.copyWorkflow(template.id)
                            .then(function(result) {
                                $state.go('templates.editWorkflowJobTemplate', {workflow_job_template_id: result.data.id}, {reload: true});
                            })
                            .catch(function (response) {
                                Wait('stop');
                                ProcessErrors($scope, response.data, response.status, null, { hdr: 'Error!',
                                    msg: 'Call to copy workflow job template failed. Return status: ' + response.status + '.'});
                            });
                        }
                        else {

                            let bodyHtml = `
                                <div class="Prompt-bodyQuery">
                                    You do not have access to all resources used by this workflow.  Resources that you don\'t have access to will not be copied and will result in an incomplete workflow.
                                </div>
                                <div class="Prompt-bodyTarget">`;

                                    // List the unified job templates user can not access
                                    if (result.data.templates_unable_to_copy.length > 0) {
                                        bodyHtml += '<div>Unified Job Templates that can not be copied<ul>';
                                        _.forOwn(result.data.templates_unable_to_copy, function(ujt) {
                                            if(ujt) {
                                                bodyHtml += '<li>' + ujt + '</li>';
                                            }
                                        });
                                        bodyHtml += '</ul></div>';
                                    }
                                    // List the prompted inventories user can not access
                                    if (result.data.inventories_unable_to_copy.length > 0) {
                                        bodyHtml += '<div>Node prompted inventories that can not be copied<ul>';
                                        _.forOwn(result.data.inventories_unable_to_copy, function(inv) {
                                            if(inv) {
                                                bodyHtml += '<li>' + inv + '</li>';
                                            }
                                        });
                                        bodyHtml += '</ul></div>';
                                    }
                                    // List the prompted credentials user can not access
                                    if (result.data.credentials_unable_to_copy.length > 0) {
                                        bodyHtml += '<div>Node prompted credentials that can not be copied<ul>';
                                        _.forOwn(result.data.credentials_unable_to_copy, function(cred) {
                                            if(cred) {
                                                bodyHtml += '<li>' + cred + '</li>';
                                            }
                                        });
                                        bodyHtml += '</ul></div>';
                                    }

                                bodyHtml += '</div>';


                            Prompt({
                                hdr: 'Copy Workflow',
                                body: bodyHtml,
                                action: function() {
                                    $('#prompt-modal').modal('hide');
                                    Wait('start');
                                    TemplateCopyService.copyWorkflow(template.id)
                                    .then(function(result) {
                                        Wait('stop');
                                        $state.go('templates.editWorkflowJobTemplate', {workflow_job_template_id: result.data.id}, {reload: true});
                                    }, function (data) {
                                        Wait('stop');
                                        ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                            msg: 'Call to copy template failed. POST returned status: ' + status });
                                    });
                                },
                                actionText: 'COPY',
                                class: 'Modal-primaryButton'
                            });
                        }
                    }
                    else {
                        Alert('Error: Unable to copy workflow job template', 'You do not have permission to perform this action.');
                    }
                }, function (data) {
                    Wait('stop');
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to copy template failed. GET returned status: ' + status });
                });
            }
            else {
                // Something went wrong - Let the user know that we're unable to copy because we don't know
                // what type of job template this is
                Alert('Error: Unable to determine template type', 'We were unable to determine this template\'s type while copying.');
            }
        }
        else {
            Alert('Error: Unable to copy job', 'Template parameter is missing');
        }
    };

    vm.deleteTemplate = function(template) {
        var action = function() {
            $('#prompt-modal').modal('hide');
            Wait('start');

            let deleteComplete = () => {
                let reloadListStateParams = null;

                if($scope.templates.length === 1 && $state.params.template_search && !_.isEmpty($state.params.template_search.page) && $state.params.template_search.page !== '1') {
                    reloadListStateParams = _.cloneDeep($state.params);
                    reloadListStateParams.template_search.page = (parseInt(reloadListStateParams.template_search.page)-1).toString();
                }

                if (parseInt($state.params.template_id) === template.id) {
                    $state.go("^", reloadListStateParams, { reload: true });
                } else {
                    $state.go('.', reloadListStateParams, {reload: true});
                }
            };

            if(template.type === "job_template") {
                jobTemplate.request('delete', template.id)
                    .then(() => {
                        deleteComplete();
                    })
                    .catch(({data, status}) => {
                        ProcessErrors($scope, data, status, null, {
                            hdr: strings.get('error.HEADER'),
                            msg: strings.get('error.CALL', {path: "" + unifiedJobTemplate.path + template.id, status})
                        });
                    })
                    .finally(function() {
                        Wait('stop');
                    });
            } else if(template.type === "workflow_job_template") {
                workflowJobTemplate.request('delete', template.id)
                    .then(() => {
                        deleteComplete();
                    })
                    .catch(({data, status}) => {
                        ProcessErrors($scope, data, status, null, {
                            hdr: strings.get('error.HEADER'),
                            msg: strings.get('error.CALL', {path: "" + unifiedJobTemplate.path + template.id, status})
                        });
                    })
                    .finally(function() {
                        Wait('stop');
                    });
            }

        };

        let deleteModalBody = `<div class="Prompt-bodyQuery">${strings.get('deleteResource.CONFIRM', 'template')}</div>`;

        Prompt({
            hdr: strings.get('deleteResource.HEADER'),
            resourceName: $filter('sanitize')(template.name),
            body: deleteModalBody,
            action: action,
            actionText: 'DELETE'
        });
    };
}

ListTemplatesController.$inject = [
    'resolvedModels',
    'JobTemplateModel',
    'WorkflowJobTemplateModel',
    'TemplatesStrings',
    '$state',
    '$scope',
    'rbacUiControlService',
    'Dataset',
    '$filter',
    'Alert',
    'InitiatePlaybookRun',
    'Prompt',
    'Wait',
    'ProcessErrors',
    'TemplateCopyService',
    '$q',
    'Empty',
    'i18n',
    'PromptService'
];

export default ListTemplatesController;
