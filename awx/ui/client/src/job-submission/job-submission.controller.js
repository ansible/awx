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
    [   '$scope', '$location', 'GetBasePath', 'Empty', 'Wait', 'Rest', 'ProcessErrors',
        'LaunchJob', '$state', 'generateList', 'InventoryList', 'SearchInit', 'PaginateInit', 'CredentialList', 'ParseTypeChange', 'GetSurveyQuestions',
        function($scope, $location, GetBasePath, Empty, Wait, Rest, ProcessErrors,
            LaunchJob, $state, GenerateList, InventoryList, SearchInit, PaginateInit, CredentialList, ParseTypeChange, GetSurveyQuestions) {

            var launch_url;

            var clearRequiredPasswords = function() {
                $scope.ssh_password_required = false;
                $scope.ssh_key_unlock_required = false;
                $scope.become_password_required = false;
                $scope.vault_password_required = false;

                $scope.ssh_password = "";
                $scope.ssh_key_unlock = "";
                $scope.become_password = "";
                $scope.vault_password = "";
            };

            var updateRequiredPasswords = function() {
                if($scope.selected_credential) {
                    if($scope.selected_credential.id === $scope.defaults.credential.id) {
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
                                case "vault_password":
                                    $scope.vault_password_required = true;
                                    break;
                            }
                        }
                    }
                    else {
                        if($scope.selected_credential.kind === "ssh"){
                            $scope.ssh_password_required = ($scope.selected_credential.password === "ASK") ? true : false;
                            $scope.ssh_key_unlock_required = ($scope.selected_credential.ssh_key_unlock === "ASK") ? true : false;
                            $scope.become_password_required = ($scope.selected_credential.become_password === "ASK") ? true : false;
                            $scope.vault_password_required = ($scope.selected_credential.vault_password === "ASK") ? true : false;
                        }
                        else {
                            clearRequiredPasswords();
                        }
                    }
                }

            };

            var launchJob = function() {
                LaunchJob({
                    scope: $scope,
                    url: launch_url
                });
            };

            // This gets things started - goes out and hits the launch endpoint (based on launch/relaunch) and
            // prepares the form fields, defauts, etc.
            $scope.init = function() {
                $scope.forms = {};
                $scope.passwords = {};

                var base = $state.current.name,
                    // As of 3.0, the only place the user can relaunch a
                    // playbook is on jobTemplates.edit (completed_jobs tab),
                    // jobs, and jobDetails $states.
                    isRelaunch = !(base === 'jobTemplates' || base === 'portalMode' || base === 'dashboard');

                if (!isRelaunch) {
                    launch_url = GetBasePath('job_templates') + $scope.submitJobId + '/launch/';
                }
                else {
                    launch_url = GetBasePath('jobs') + $scope.submitJobId + '/relaunch/';
                }

                // Get the job or job_template record
                Wait('start');
                Rest.setUrl(launch_url);
                Rest.get()
                .success(function (data) {

                    // Put all the data that we get back about the launch onto scope
                    angular.extend($scope, data);

                    // General catch-all for "other prompts" - used in this link function and to hide the Other Prompts tab when
                    // it should be hidden
                    $scope.has_other_prompts = (data.ask_job_type_on_launch || data.ask_limit_on_launch || data.ask_tags_on_launch || data.ask_variables_on_launch) ? true : false;
                    $scope.password_needed = data.passwords_needed_to_start && data.passwords_needed_to_start.length > 0;
                    $scope.has_default_inventory = data.defaults && data.defaults.inventory && data.defaults.inventory.id;
                    $scope.has_default_credential = data.defaults && data.defaults.credential && data.defaults.credential.id;

                    $scope.other_prompt_data = {};

                    if($scope.ask_job_type_on_launch) {
                        $scope.other_prompt_data.job_type = (data.defaults && data.defaults.job_type) ? data.defaults.job_type : "";
                    }

                    if($scope.ask_limit_on_launch) {
                        $scope.other_prompt_data.limit = (data.defaults && data.defaults.limit) ? data.defaults.limit : "";
                    }

                    if($scope.ask_tags_on_launch) {
                        $scope.other_prompt_data.job_tags = (data.defaults && data.defaults.job_tags) ? data.defaults.job_tags : "";
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
                        $scope.selected_credential = angular.copy($scope.defaults.credential);
                        updateRequiredPasswords();
                    }

                    if( (isRelaunch && !$scope.password_needed) || (!isRelaunch && $scope.can_start_without_user_input && !$scope.ask_inventory_on_launch && !$scope.ask_credential_on_launch && !$scope.has_other_prompts && !$scope.survey_enabled)) {
                        // The job can be launched if
                        // a) It's a relaunch and no passwords are needed
                        // or
                        // b) It's not a relaunch and there's not any prompting/surveys
                        launchJob();
                        Wait('stop');
                    }
                    else {

                        var initiateModal = function() {
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

                        if(isRelaunch) {
                            // Go out and get some of the job details like inv, cred, name
                            Rest.setUrl(GetBasePath('jobs') + $scope.submitJobId);
                            Rest.get()
                            .success(function (jobDetailData) {
                                $scope.job_template_data = {
                                    name: jobDetailData.name
                                };
                                $scope.defaults = {};
                                if(jobDetailData.summary_fields.inventory) {
                                    $scope.defaults.inventory = angular.copy(jobDetailData.summary_fields.inventory);
                                    $scope.selected_inventory = angular.copy(jobDetailData.summary_fields.inventory);
                                }
                                if(jobDetailData.summary_fields.credential) {
                                    $scope.defaults.credential = angular.copy(jobDetailData.summary_fields.credential);
                                    $scope.selected_credential = angular.copy(jobDetailData.summary_fields.credential);
                                    updateRequiredPasswords();
                                }
                                initiateModal();
                            })
                            .error(function(data, status) {
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
                .error(function (data, status) {
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

            $scope.getListsAndSurvey = function() {
                if($scope.ask_inventory_on_launch) {
                    var inventory_url = GetBasePath('inventory');

                    var invList = _.cloneDeep(InventoryList);
                    invList.fields.status.searchable = false;
                    invList.fields.organization.searchable = false;
                    invList.fields.has_inventory_sources.searchable = false;
                    invList.fields.has_active_failures.searchable = false;
                    invList.fields.inventory_sources_with_failures.searchable = false;

                    GenerateList.inject(invList, {
                        mode: 'lookup',
                        id: 'job-submission-inventory-lookup',
                        scope: $scope,
                        input_type: 'radio'
                    });

                    SearchInit({
                        scope: $scope,
                        set: InventoryList.name,
                        list: InventoryList,
                        url: inventory_url
                    });

                    PaginateInit({
                        scope: $scope,
                        list: InventoryList,
                        url: inventory_url,
                        mode: 'lookup'
                    });

                    $scope.search(InventoryList.iterator);

                    $scope.$watchCollection('inventories', function () {
                        if($scope.selected_inventory) {
                            // Loop across the inventories and see if one of them should be "checked"
                            $scope.inventories.forEach(function(row, i) {
                                if (row.id === $scope.selected_inventory.id) {
                                    $scope.inventories[i].checked = 1;
                                }
                                else {
                                    $scope.inventories[i].checked = 0;
                                }
                            });
                        }
                    });
                }
                if($scope.ask_credential_on_launch) {
                    var credential_url = GetBasePath('credentials') + '?kind=ssh';

                    var credList = _.cloneDeep(CredentialList);
                    credList.basePath = GetBasePath('credentials') + '?kind=ssh';
                    credList.fields.description.searchable = false;
                    credList.fields.kind.searchable = false;

                    GenerateList.inject(credList, {
                        mode: 'lookup',
                        id: 'job-submission-credential-lookup',
                        scope: $scope,
                        input_type: 'radio'
                    });

                    SearchInit({
                        scope: $scope,
                        set: CredentialList.name,
                        list: CredentialList,
                        url: credential_url
                    });

                    PaginateInit({
                        scope: $scope,
                        list: CredentialList,
                        url: credential_url,
                        mode: 'lookup'
                    });

                    $scope.search(CredentialList.iterator);

                    $scope.$watchCollection('credentials', function () {
                        if($scope.selected_credential) {
                            // Loop across the inventories and see if one of them should be "checked"
                            $scope.credentials.forEach(function(row, i) {
                                if (row.id === $scope.selected_credential.id) {
                                    $scope.credentials[i].checked = 1;
                                }
                                else {
                                    $scope.credentials[i].checked = 0;
                                }
                            });
                        }
                    });
                }
                if($scope.survey_enabled) {
                    GetSurveyQuestions({
                        scope: $scope,
                        id: $scope.submitJobId
                    });

                }
            };

            $scope.revertToDefaultInventory = function() {
                if($scope.has_default_inventory) {
                    $scope.selected_inventory = angular.copy($scope.defaults.inventory);

                    // Loop across inventories and set update the "checked" attribute for each row
                    $scope.inventories.forEach(function(row, i) {
                        if (row.id === $scope.selected_inventory.id) {
                            $scope.inventories[i].checked = 1;
                        } else {
                            $scope.inventories[i].checked = 0;
                        }
                    });
                }
            };

            $scope.revertToDefaultCredential = function() {
                if($scope.has_default_credential) {
                    $scope.selected_credential = angular.copy($scope.defaults.credential);
                    updateRequiredPasswords();

                    // Loop across credentials and set update the "checked" attribute for each row
                    $scope.credentials.forEach(function(row, i) {
                        if (row.id === $scope.selected_credential.id) {
                            $scope.credentials[i].checked = 1;
                        } else {
                            $scope.credentials[i].checked = 0;
                        }
                    });
                }
            };

            $scope.toggle_inventory = function(id) {
                $scope.inventories.forEach(function(row, i) {
                    if (row.id === id) {
                        $scope.selected_inventory = angular.copy(row);
                        $scope.inventories[i].checked = 1;
                    } else {
                        $scope.inventories[i].checked = 0;
                    }
                });
            };

            $scope.toggle_credential = function(id) {
                $scope.credentials.forEach(function(row, i) {
                    if (row.id === id) {
                        $scope.selected_credential = angular.copy(row);
                        updateRequiredPasswords();
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
                    if($scope.selected_credential && $scope.forms.credentialpasswords && $scope.forms.credentialpasswords.$valid) {
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

            $scope.updateParseType = function() {
                // This is what the ParseTypeChange factory is expecting
                // It shares the same scope with this directive and will
                // pull the new value of parseType out to determine which
                // direction to convert the extra vars
                $scope.parseType = $scope.other_prompt_data.parseType;
                $scope.parseTypeChange();
            };

        }
    ];
