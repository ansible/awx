/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:JobSubmission
 * @description This controller's for the Job Submission Modal
* The job-submission directive is intended to handle job launch/relaunch from a playbook.  There are 4 potential steps involved in launching a job:
*
*   Select an Inventory
*   Select a Credential
*   Extra prompts (extra vars, limit, job type, job tags)
*   Fill in survey
*
* #Workflow when user hits launch button
*
* A 'get' call is made to the API's 'job_templates/:job_template_id/launch' endpoint for that job template. The response from the API will specify
*
*```
*    "credential_needed_to_start": true,
*    "can_start_without_user_input": false,
*    "ask_variables_on_launch": false,
*    "passwords_needed_to_start": [],
*    "variables_needed_to_start": [],
*    "survey_enabled": false
*```
* #Step 1 - Hit the launch/relaunch endpoint
*
* The launch/relaunch endpoint(s) let us know what the default values are for a particular job template.  It also lets us know what the creator of
* the job template selected as "promptable" fields.
*
* #Step 2 - Gather inv/credential lists and job template survey questions
*
* If the job template allows for inventory or credential prompting then we need to go out and get the available inventories and credentials for the
* launching user.  We also go out and get the survey from its endpoint if a survey has been created and is enabled for this job template (getsurveyquestions.factory).
*
* #Step 3 - Fill out the job launch form
*
* No server calls needed as a user fills out the form.  Note that if no user input is required (no prompts, no passwords) then we skip ahead to the next
* step.
*
* #Step 4 - Launch the job: LaunchJob
*
* This is maybe the most crucial step. We have setup everything we need in order to gather information from the user and now we want to be sure
* we handle it correctly. And there are many scenarios to take into account. The first scenario we check for is is ``survey_enabled=true`` and
*  ``prompt_for_vars=false``, in which case we want to make sure to include the extra_vars from the job template in the data being
* sent to the API (it is important to note that anything specified in the extra vars on job submission will override vars specified in the job template.
* Likewise, any variables specified in the extra vars that are duplicated by the survey vars, will get overridden by the survey vars).
* If the previous scenario is NOT the case, then we continue to gather the modal's answers regularly: gather the passwords, then the extra_vars, then
* any survey results. Also note that we must gather any required survey answers, as well as any optional survey answers that happened to be provided
* by the user. We also include the credential that was chosen if the user was prompted to select a credential.
* At this point we have all the info we need and we are almost ready to perform a POST to the '/launch' endpoint. We must lastly check
* if the user was not prompted for anything and therefore we don't want to pass any extra_vars to the POST. Once this is done we
* make the REST POST call and provide all the data to hte API. The response from the API will be the job ID, which is used to redirect the user
* to the job detail page for that job run.
*
* @Usage
* This is usage information.
*/

export default
    [   '$scope', 'GetBasePath', 'Wait', 'Rest', 'ProcessErrors',
        'LaunchJob', '$state', 'InventoryList', 'CredentialList', 'ParseTypeChange',
        function($scope, GetBasePath, Wait, Rest, ProcessErrors,
            LaunchJob, $state, InventoryList, CredentialList, ParseTypeChange) {

            var launch_url;

            var clearRequiredPasswords = function() {
                $scope.ssh_password_required = false;
                $scope.ssh_key_unlock_required = false;
                $scope.become_password_required = false;

                $scope.ssh_password = "";
                $scope.ssh_key_unlock = "";
                $scope.become_password = "";
            };

            var launchJob = function() {
                LaunchJob({
                    scope: $scope,
                    url: launch_url,
                    submitJobType: $scope.submitJobType,
                    relaunchHostType: $scope.relaunchHostType
                });
            };

            // This gets things started - goes out and hits the launch endpoint (based on launch/relaunch) and
            // prepares the form fields, defauts, etc.
            $scope.init = function() {
                $scope.forms = {};
                $scope.passwords = {};
                $scope.selected_credentials = {
                    machine: null,
                    extra: []
                };

                // As of 3.0, the only place the user can relaunch a
                // playbook is on jobTemplates.edit (completed_jobs tab),
                // jobs, and jobResults $states.

                if (!$scope.submitJobRelaunch) {
                    if($scope.submitJobType && $scope.submitJobType === 'job_template') {
                        launch_url = GetBasePath('job_templates') + $scope.submitJobId + '/launch/';
                    }
                    else if($scope.submitJobType && $scope.submitJobType === 'workflow_job_template') {
                        launch_url = GetBasePath('workflow_job_templates') + $scope.submitJobId + '/launch/';
                    }
                }
                else {
                    if($scope.submitJobType && $scope.submitJobType === 'workflow_job') {
                        launch_url = GetBasePath('workflow_jobs') + $scope.submitJobId + '/relaunch/';
                    }
                    else {
                        launch_url = GetBasePath('jobs') + $scope.submitJobId + '/relaunch/';
                    }
                }

                $scope.$watch('selected_credentials.machine', function(){
                    if($scope.selected_credentials.machine) {
                        if($scope.selected_credentials.machine.id === $scope.defaults.credential.id) {
                            clearRequiredPasswords();
                            for(var i=0; i<$scope.passwords_needed_to_start.length; i++) {
                                var password = $scope.passwords_needed_to_start[i];
                                switch(password) {
                                    case "ssh_password":
                                        $scope.ssh_password_required = true;
                                        break;
                                    case "ssh_key_unlock":
                                        $scope.ssh_key_unlock_required = true;
                                        break;
                                    case "become_password":
                                        $scope.become_password_required = true;
                                        break;
                                }
                            }
                        }
                        else {
                            $scope.ssh_password_required = ($scope.selected_credentials.machine.inputs && $scope.selected_credentials.machine.inputs.password === "ASK") ? true : false;
                            $scope.ssh_key_unlock_required = ($scope.selected_credentials.machine.inputs && $scope.selected_credentials.machine.inputs.ssh_key_unlock === "ASK") ? true : false;
                            $scope.become_password_required = $scope.selected_credentials.machine.inputs && ($scope.selected_credentials.machine.inputs.become_password === "ASK") ? true : false;
                        }
                    }
                    else {
                        clearRequiredPasswords();
                    }
                });

                // Get the job or job_template record
                Wait('start');
                Rest.setUrl(launch_url);
                Rest.get()
                .then(({data}) => {

                    // Put all the data that we get back about the launch onto scope
                    angular.extend($scope, data);

                    // General catch-all for "other prompts" - used in this link function and to hide the Other Prompts tab when
                    // it should be hidden
                    $scope.has_other_prompts = (data.ask_verbosity_on_launch || data.ask_job_type_on_launch || data.ask_limit_on_launch || data.ask_tags_on_launch || data.ask_skip_tags_on_launch || data.ask_variables_on_launch || data.ask_diff_mode_on_launch) ? true : false;
                    $scope.password_needed = data.passwords_needed_to_start && data.passwords_needed_to_start.length > 0;
                    $scope.has_default_inventory = data.defaults && data.defaults.inventory && data.defaults.inventory.id;
                    $scope.has_default_credential = data.defaults && data.defaults.credential && data.defaults.credential.id;
                    $scope.has_default_vault_credential = data.defaults && data.defaults.vault_credential && data.defaults.vault_credential.id;
                    $scope.vault_password_required = ($scope.password_needed && data.passwords_needed_to_start.includes('vault_password'));
                    $scope.has_default_extra_credentials = data.defaults && data.defaults.extra_credentials && data.defaults.extra_credentials.length > 0;

                    $scope.other_prompt_data = {};

                    let getChoices = (options, lookup) => {
                        return _.get(options, lookup, []).map(c => ({label: c[1], value: c[0]}));
                    };

                    let getChoiceFromValue = (choices, value) => {
                        return _.find(choices, item => item.value === value);
                    };

                    if ($scope.has_other_prompts) {
                        Rest.options()
                        .then(options => {
                            if ($scope.ask_job_type_on_launch) {
                                let choices = getChoices(options.data, 'actions.POST.job_type.choices');
                                let initialValue = _.get(data, 'defaults.job_type');
                                let initialChoice = getChoiceFromValue(choices, initialValue);
                                $scope.other_prompt_data.job_type_options = choices;
                                $scope.other_prompt_data.job_type = initialChoice;
                            }
                            if ($scope.ask_verbosity_on_launch) {
                                let choices = getChoices(options.data, 'actions.POST.verbosity.choices');
                                let initialValue = _.get(data, 'defaults.verbosity');
                                let initialChoice = getChoiceFromValue(choices, initialValue);
                                $scope.other_prompt_data.verbosity_options = choices;
                                $scope.other_prompt_data.verbosity = initialChoice;
                            }
                        })
                        .catch((error) => {
                            ProcessErrors($scope, error.data, error.status, null, {
                                hdr: 'Error!',
                                msg: `Failed to get ${launch_url}. OPTIONS status: ${error.status}`
                            });
                        });
                    }

                    if($scope.ask_limit_on_launch) {
                        $scope.other_prompt_data.limit = (data.defaults && data.defaults.limit) ? data.defaults.limit : "";
                    }

                    if($scope.ask_tags_on_launch) {
                        $scope.other_prompt_data.job_tags_options = (data.defaults && data.defaults.job_tags) ? data.defaults.job_tags.split(',')
                            .map((i) => ({name: i, label: i, value: i})) : [];
                        $scope.other_prompt_data.job_tags = $scope.other_prompt_data.job_tags_options;
                    }

                    if($scope.ask_skip_tags_on_launch) {
                        $scope.other_prompt_data.skip_tags_options = (data.defaults && data.defaults.skip_tags) ? data.defaults.skip_tags.split(',')
                            .map((i) => ({name: i, label: i, value: i})) : [];
                        $scope.other_prompt_data.skip_tags = $scope.other_prompt_data.skip_tags_options;
                    }

                    if($scope.ask_diff_mode_on_launch) {
                        $scope.other_prompt_data.diff_mode = (data.defaults && data.defaults.diff_mode) ? data.defaults.diff_mode : false;
                    }

                    if($scope.ask_variables_on_launch) {
                        $scope.jobLaunchVariables = (data.defaults && data.defaults.extra_vars) ? data.defaults.extra_vars : "---";
                        $scope.other_prompt_data.parseType = 'yaml';
                        $scope.parseType = 'yaml';
                    }

                    if($scope.has_default_inventory) {
                        $scope.selected_inventory = angular.copy($scope.defaults.inventory);
                    }

                    if($scope.has_default_credential) {
                        $scope.selected_credentials.machine = angular.copy($scope.defaults.credential);
                    }

                    if($scope.has_default_vault_credential) {
                        $scope.selected_credentials.vault = angular.copy($scope.defaults.vault_credential);
                    }

                    if($scope.has_default_extra_credentials) {
                        $scope.selected_credentials.extra = angular.copy($scope.defaults.extra_credentials);
                    }

                    if( ($scope.submitJobType === 'workflow_job_template' && !$scope.survey_enabled) || ($scope.submitJobRelaunch && !$scope.password_needed) || (!$scope.submitJobRelaunch && $scope.can_start_without_user_input && !$scope.ask_inventory_on_launch && !$scope.ask_credential_on_launch && !$scope.has_other_prompts && !$scope.survey_enabled)) {
                        // The job can be launched if
                        // a) It's a relaunch and no passwords are needed
                        // or
                        // b) It's not a relaunch and there's not any prompting/surveys
                        launchJob();
                        Wait('stop');
                    }
                    else {

                        var initiateModal = function() {

                            // Go out and get the credential types
                            Rest.setUrl(GetBasePath('credential_types'));
                            Rest.get()
                            .then( (response) => {
                                let credentialTypeData = response.data;
                                let credential_types = {};
                                $scope.credentialTypeOptions = [];
                                credentialTypeData.results.forEach((credentialType => {
                                    credential_types[credentialType.id] = credentialType;
                                    if(credentialType.kind.match(/^(machine|cloud|net|ssh)$/)) {
                                        $scope.credentialTypeOptions.push({
                                            name: credentialType.name,
                                            value: credentialType.id
                                        });
                                    }
                                }));
                                $scope.credential_types = credential_types;
                            })
                            .catch(({data, status}) => {
                                ProcessErrors($scope, data, status, null, {
                                    hdr: 'Error!',
                                    msg: 'Failed to get credential types. GET status: ' + status
                                });
                            });

                            // Figure out which step the user needs to start on
                            if($scope.ask_inventory_on_launch) {
                                $scope.setStep("inventory", true);
                            }
                            else if($scope.ask_credential_on_launch || $scope.password_needed) {
                                $scope.setStep("credential", true);
                            }
                            else if($scope.has_other_prompts) {
                                $scope.setStep("otherprompts", true);
                            }
                            else if($scope.survey_enabled) {
                                $scope.setStep("survey", true);
                            }

                            $scope.openLaunchModal();
                        };

                        if($scope.submitJobRelaunch) {
                            // Go out and get some of the job details like inv, cred, name
                            Rest.setUrl(GetBasePath('jobs') + $scope.submitJobId);
                            Rest.get()
                            .then( (response) => {
                                let jobResultData = response.data;
                                $scope.job_template_data = {
                                    name: jobResultData.name
                                };
                                $scope.defaults = {};
                                if(jobResultData.summary_fields.inventory) {
                                    $scope.defaults.inventory = angular.copy(jobResultData.summary_fields.inventory);
                                    $scope.selected_inventory = angular.copy(jobResultData.summary_fields.inventory);
                                }
                                if(jobResultData.summary_fields.credential) {
                                    $scope.defaults.credential = angular.copy(jobResultData.summary_fields.credential);
                                    $scope.selected_credentials.machine = angular.copy(jobResultData.summary_fields.credential);
                                }
                                initiateModal();
                            })
                            .catch(({data, status}) => {
                                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                msg: 'Failed to get job details. GET returned status: ' + status });
                            });
                        }
                        else {
                            // Move forward with the modal
                            initiateModal();
                        }

                    }

                })
                .catch(({data, status}) => {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to get job template details. GET returned status: ' + status });
                });
            };

            $scope.setStep = function(step, initialStep) {
                $scope.step = step;

                if(step === "credential") {
                    $scope.credentialTabEnabled = true;
                }
                else if(step === "otherprompts") {
                    $scope.otherPromptsTabEnabled = true;

                    if(!initialStep && $scope.step === 'otherprompts' && $scope.ask_variables_on_launch && !$scope.extra_vars_code_mirror_loaded) {
                        ParseTypeChange({
                            scope: $scope,
                            variable: 'jobLaunchVariables',
                            field_id: 'job_launch_variables'
                        });

                        $scope.extra_vars_code_mirror_loaded = true;
                    }
                }
                else if(step === "survey") {
                    $scope.surveyTabEnabled = true;
                }

            };

            $scope.revertToDefaultInventory = function() {
                if($scope.has_default_inventory) {
                    $scope.selected_inventory = angular.copy($scope.defaults.inventory);
                }
                else {
                    $scope.selected_inventory = null;
                }
            };

            $scope.revertToDefaultCredentials = function() {
                if($scope.has_default_credential) {
                    $scope.selected_credentials.machine = angular.copy($scope.defaults.credential);
                }
                else {
                    $scope.selected_credentials.machine = null;
                }
                if($scope.has_default_vault_credential) {
                    $scope.selected_credentials.vault = angular.copy($scope.defaults.vault_credential);
                }
                else {
                    $scope.selected_credentials.vault = null;
                }
                if($scope.has_default_extra_credentials) {
                    $scope.selected_credentials.extra = angular.copy($scope.defaults.extra_credentials);
                }
                else {
                    $scope.selected_credentials.extra = [];
                }
            };

            $scope.toggle_credential = function(cred) {
                $scope.credentials.forEach(function(row, i) {
                    if (row.id === cred.id) {
                        $scope.selected_credentials.machine = angular.copy(row);
                        $scope.credentials[i].checked = 1;
                    } else {
                        $scope.credentials[i].checked = 0;
                    }
                });
            };

            $scope.getActionButtonText = function() {
                if($scope.step === "inventory") {
                    return ($scope.ask_credential_on_launch || $scope.password_needed || $scope.has_other_prompts || $scope.survey_enabled) ? "NEXT" : "LAUNCH";
                }
                else if($scope.step === "credential") {
                    return ($scope.has_other_prompts || $scope.survey_enabled) ? "NEXT" : "LAUNCH";
                }
                else if($scope.step === "otherprompts") {
                    return ($scope.survey_enabled) ? "NEXT" : "LAUNCH";
                }
                else if($scope.step === "survey") {
                    return "LAUNCH";
                }
            };

            $scope.actionButtonDisabled = function() {
                if($scope.step === "inventory") {
                    if($scope.selected_inventory) {
                        return false;
                    }
                    else {
                        $scope.credentialTabEnabled = false;
                        $scope.otherPromptsTabEnabled = false;
                        $scope.surveyTabEnabled = false;
                        return true;
                    }
                }
                else if($scope.step === "credential") {
                    if(($scope.selected_credentials.machine || $scope.selected_credentials.vault) && $scope.forms.credentialpasswords && $scope.forms.credentialpasswords.$valid) {
                        return false;
                    }
                    else {
                        $scope.otherPromptsTabEnabled = false;
                        $scope.surveyTabEnabled = false;
                        return true;
                    }
                }
                else if($scope.step === "otherprompts") {
                    if($scope.forms.otherprompts.$valid) {
                        return false;
                    }
                    else {
                        $scope.surveyTabEnabled = false;
                        return true;
                    }
                }
                else if($scope.step === "survey") {
                    if($scope.forms.survey.$valid) {
                        return false;
                    }
                    else {
                        return true;
                    }
                }

            };

            $scope.takeAction = function() {
                if($scope.step === "inventory") {
                    // Check to see if there's another step after this one
                    if($scope.ask_credential_on_launch || $scope.password_needed) {
                        $scope.setStep("credential");
                    }
                    else if($scope.has_other_prompts) {
                        $scope.setStep("otherprompts");
                    }
                    else if($scope.survey_enabled) {
                        $scope.setStep("survey");
                    }
                    else {
                        launchJob();
                    }
                }
                else if($scope.step === "credential") {
                    if($scope.has_other_prompts) {
                        $scope.setStep("otherprompts");
                    }
                    else if($scope.survey_enabled) {
                        $scope.setStep("survey");
                    }
                    else {
                        launchJob();
                    }
                }
                else if($scope.step === "otherprompts") {
                    if($scope.survey_enabled) {
                        $scope.setStep("survey");
                    }
                    else {
                        launchJob();
                    }
                }
                else {
                    launchJob();
                }
            };

            $scope.toggleForm = function(key) {
                $scope.other_prompt_data[key] = !$scope.other_prompt_data[key];
            };

            $scope.updateParseType = function() {
                // This is what the ParseTypeChange factory is expecting
                // It shares the same scope with this directive and will
                // pull the new value of parseType out to determine which
                // direction to convert the extra vars

                $scope.parseType = $scope.other_prompt_data.parseType;
                $scope.parseTypeChange('parseType', 'jobLaunchVariables');
            };

            $scope.showRevertCredentials = function(){
                let machineCredentialMatches = true;
                let extraCredentialsMatch = true;

                if($scope.defaults.credential && $scope.defaults.credential.id) {
                    if(!$scope.selected_credentials.machine || ($scope.selected_credentials.machine && $scope.selected_credentials.machine.id !== $scope.defaults.credential.id)) {
                        machineCredentialMatches = false;
                    }
                }
                else {
                    if($scope.selected_credentials.machine && $scope.selected_credentials.machine.id) {
                        machineCredentialMatches = false;
                    }
                }

                if($scope.defaults.extra_credentials && $scope.defaults.extra_credentials.length > 0) {
                    if($scope.selected_credentials.extra && $scope.selected_credentials.extra.length > 0) {
                        if($scope.defaults.extra_credentials.length !== $scope.selected_credentials.extra.length) {
                            extraCredentialsMatch = false;
                        }
                        else {
                            $scope.defaults.extra_credentials.forEach((defaultExtraCredential) =>{
                                let matchesSelected = false;
                                $scope.selected_credentials.extra.forEach((selectedExtraCredential) =>{
                                    if(defaultExtraCredential.id === selectedExtraCredential.id) {
                                        matchesSelected = true;
                                    }
                                });
                                if(!matchesSelected) {
                                    extraCredentialsMatch = false;
                                }
                            });
                        }

                    }
                    else {
                        extraCredentialsMatch = false;
                    }
                }
                else {
                    if($scope.selected_credentials.extra && $scope.selected_credentials.extra.length > 0) {
                        extraCredentialsMatch = false;
                    }
                }

                return machineCredentialMatches && extraCredentialsMatch ? false : true;
            };

            $scope.$on('inventorySelected', function(evt, selectedRow){
                $scope.selected_inventory = _.cloneDeep(selectedRow);
            });

            $scope.deleteMachineCred = function() {
                $scope.selected_credentials.machine = null;
            };

            $scope.deleteExtraCred = function(index) {
                $scope.selected_credentials.extra.splice(index, 1);
            };

            $scope.deleteSelectedInventory = function() {
                $scope.selected_inventory = null;
            };

        }
    ];
