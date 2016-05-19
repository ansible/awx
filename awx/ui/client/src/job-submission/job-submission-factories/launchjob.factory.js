export default
    function LaunchJob(Rest, Wait, ProcessErrors, ToJSON, Empty, GetBasePath, $state, $location) {

            // This factory gathers up all the job launch data and POST's it.

            // TODO: outline how these things are gathered

            return function (params) {
                var scope = params.scope,
                job_launch_data = {},
                url = params.url,
                vars_url = GetBasePath('job_templates')+scope.job_template_id + '/',
                base = $location.path().replace(/^\//, '').split('/')[0],
                extra_vars;

                //found it easier to assume that there will be extra vars, and then check for a blank object at the end
                job_launch_data.extra_vars = {};

                //build the data object to be sent to the job launch endpoint. Any variables gathered from the survey and the extra variables text editor are inserted into the extra_vars dict of the job_launch_data
                var buildData = function() {
                    if(scope.ssh_password_required) {
                        job_launch_data.ssh_password = scope.passwords.ssh_password;
                    }
                    if(scope.ssh_key_unlock_required) {
                        job_launch_data.ssh_key_unlock = scope.passwords.ssh_key_unlock;
                    }
                    if(scope.become_password_required) {
                        job_launch_data.become_password = scope.passwords.become_password;
                    }
                    if(scope.vault_password_required) {
                        job_launch_data.vault_password = scope.passwords.vault_password;
                    }

                    if(scope.ask_variables_on_launch){
                        extra_vars = ToJSON(scope.parseType, scope.jobLaunchVariables, false);
                        if(!Empty(extra_vars)){
                            $.each(extra_vars, function(key,value){
                                job_launch_data.extra_vars[key] = value;
                            });
                        }

                    }

                    if(scope.ask_tags_on_launch && scope.other_prompt_data && scope.other_prompt_data.job_tags){
                        job_launch_data.job_tags = scope.other_prompt_data.job_tags;
                    }

                    if(scope.ask_limit_on_launch && scope.other_prompt_data && scope.other_prompt_data.limit){
                        job_launch_data.limit = scope.other_prompt_data.limit;
                    }

                    if(scope.ask_job_type_on_launch && scope.other_prompt_data && scope.other_prompt_data.job_type) {
                        job_launch_data.job_type = scope.other_prompt_data.job_type;
                    }

                    if(scope.survey_enabled===true){
                        for (var i=0; i < scope.survey_questions.length; i++){
                            var fld = scope.survey_questions[i].variable;
                            // grab all survey questions that have answers
                            if(scope.survey_questions[i].required || (scope.survey_questions[i].required === false && scope.survey_questions[i].model.toString()!=="")) {
                                job_launch_data.extra_vars[fld] = scope.survey_questions[i].model;
                            }

                            if(scope.survey_questions[i].required === false && _.isEmpty(scope.survey_questions[i].model)) {
                                switch (scope.survey_questions[i].type) {
                                    // for optional text and text-areas, submit a blank string if min length is 0
                                    // -- this is confusing, for an explanation see:
                                    //    http://docs.ansible.com/ansible-tower/latest/html/userguide/job_templates.html#optional-survey-questions
                                    //
                                    case "text":
                                    case "textarea":
                                    if (scope.survey_questions[i].min === 0) {
                                        job_launch_data.extra_vars[fld] = "";
                                    }
                                    break;

                                    // for optional select lists, if they are left blank make sure we submit
                                    // a value that the API will consider "empty"
                                    //
                                    case "multiplechoice":
                                        job_launch_data.extra_vars[fld] = "";
                                        break;
                                    case "multiselect":
                                        job_launch_data.extra_vars[fld] = [];
                                        break;
                                }
                            }
                        }
                    }

                    // include the inventory used if the user was prompted to choose a cred
                    if(scope.ask_inventory_on_launch && !Empty(scope.selected_inventory)){
                        job_launch_data.inventory_id = scope.selected_inventory.id;
                    }

                    // include the credential used if the user was prompted to choose a cred
                    if(scope.ask_credential_on_launch && !Empty(scope.selected_credential)){
                        job_launch_data.credential_id = scope.selected_credential.id;
                    }

                    // If the extra_vars dict is empty, we don't want to include it if we didn't prompt for anything.
                    if(jQuery.isEmptyObject(job_launch_data.extra_vars)===true && scope.prompt_for_vars===false){
                        delete job_launch_data.extra_vars;
                    }

                    Rest.setUrl(url);
                    Rest.post(job_launch_data)
                    .success(function(data) {
                        Wait('stop');
                        var job = data.job || data.system_job;
                        if((scope.portalMode===false || scope.$parent.portalMode===false ) && Empty(data.system_job) || (base === 'home')){
                            // use $state.go with reload: true option to re-instantiate sockets in
                            $state.go('jobDetail', {id: job}, {reload: true});
                        }
                        scope.clearDialog();
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed updating job ' + scope.job_template_id + ' with variables. POST returned: ' + status });
                    });
                };

                //gather the extra vars from the job template if survey is enabled and prompt for vars is false
                var getExtraVars = function() {
                    Rest.setUrl(vars_url);
                    Rest.get()
                    .success(function (data) {
                        if(!Empty(data.extra_vars)){
                            data.extra_vars = ToJSON('yaml',  data.extra_vars, false);
                            $.each(data.extra_vars, function(key,value){
                                job_launch_data.extra_vars[key] = value;
                            });
                        }
                        buildData();
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, { hdr: 'Error!',
                        msg: 'Failed to retrieve job template extra variables.'  });
                    });
                };

                // if the user has a survey and does not have 'prompt for vars' selected, then we want to
                // include the extra vars from the job template in the job launch. so first check for these conditions
                // and then overlay any survey vars over those.
                if(scope.prompt_for_vars===false && scope.survey_enabled===true){
                    getExtraVars();
                }
                else {
                    buildData();
                }

            };
        }

LaunchJob.$inject =
    [   'Rest',
        'Wait',
        'ProcessErrors',
        'ToJSON',
        'Empty',
        'GetBasePath',
        '$state',
        '$location'
    ];
