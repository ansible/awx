export default
    function SchedulePost(Rest, ProcessErrors, RRuleToAPI, Wait, $q) {
        return function(params) {
            var scope = params.scope,
                url = params.url,
                scheduler = params.scheduler,
                mode = params.mode,
                schedule = (params.schedule) ? params.schedule : {},
                promptData = params.promptData,
                newSchedule, rrule, extra_vars;
            let deferred = $q.defer();
            if (scheduler.isValid()) {
                Wait('start');
                newSchedule = scheduler.getValue();
                rrule = scheduler.getRRule();
                schedule.name = newSchedule.name;
                schedule.rrule = RRuleToAPI(rrule.toString(), scope);
                schedule.description = (/error/.test(rrule.toText())) ? '' : rrule.toText();

                if (scope.isFactCleanup) {
                    extra_vars = {
                        "older_than": scope.scheduler_form.keep_amount.$viewValue + scope.scheduler_form.keep_unit.$viewValue.value,
                        "granularity": scope.scheduler_form.granularity_keep_amount.$viewValue + scope.scheduler_form.granularity_keep_unit.$viewValue.value
                    };
                    schedule.extra_data = JSON.stringify(extra_vars);
                } else if (scope.cleanupJob) {
                    extra_vars = {
                        "days" : scope.scheduler_form.schedulerPurgeDays.$viewValue
                    };
                    schedule.extra_data = JSON.stringify(extra_vars);
                }
                else if(scope.extraVars){
                    schedule.extra_data = scope.parseType === 'yaml' ?
                        (scope.extraVars === '---' ? "" : jsyaml.safeLoad(scope.extraVars)) : scope.extraVars;
                }

                if(promptData) {
                    if(promptData.launchConf.survey_enabled){
                        for (var i=0; i < promptData.surveyQuestions.length; i++){
                            var fld = promptData.surveyQuestions[i].variable;
                            // grab all survey questions that have answers
                            if(promptData.surveyQuestions[i].required || (promptData.surveyQuestions[i].required === false && promptData.surveyQuestions[i].model.toString()!=="")) {
                                if(!schedule.extra_data) {
                                    schedule.extra_data = {};
                                }
                                schedule.extra_data[fld] = promptData.surveyQuestions[i].model;
                            }

                            if(promptData.surveyQuestions[i].required === false && _.isEmpty(promptData.surveyQuestions[i].model)) {
                                switch (promptData.surveyQuestions[i].type) {
                                    // for optional text and text-areas, submit a blank string if min length is 0
                                    // -- this is confusing, for an explanation see:
                                    //    http://docs.ansible.com/ansible-tower/latest/html/userguide/job_templates.html#optional-survey-questions
                                    //
                                    case "text":
                                    case "textarea":
                                    if (promptData.surveyQuestions[i].min === 0) {
                                        schedule.extra_data[fld] = "";
                                    }
                                    break;
                                }
                            }
                        }
                    }

                    if(_.has(promptData, 'prompts.jobType.value.value') && _.get(promptData, 'launchConf.ask_job_type_on_launch')) {
                        schedule.job_type = promptData.prompts.jobType.templateDefault === promptData.prompts.jobType.value.value ? null : promptData.prompts.jobType.value.value;
                    }
                    if(_.has(promptData, 'prompts.tags.value') && _.get(promptData, 'launchConf.ask_tags_on_launch')){
                        let templateDefaultJobTags = promptData.prompts.tags.templateDefault.split(',');
                        schedule.job_tags = (_.isEqual(templateDefaultJobTags.sort(), promptData.prompts.tags.value.map(a => a.value).sort())) ? null : promptData.prompts.tags.value.map(a => a.value).join();
                    }
                    if(_.has(promptData, 'prompts.skipTags.value') && _.get(promptData, 'launchConf.ask_skip_tags_on_launch')){
                        let templateDefaultSkipTags = promptData.prompts.skipTags.templateDefault.split(',');
                        schedule.skip_tags = (_.isEqual(templateDefaultSkipTags.sort(), promptData.prompts.skipTags.value.map(a => a.value).sort())) ? null : promptData.prompts.skipTags.value.map(a => a.value).join();
                    }
                    if(_.has(promptData, 'prompts.limit.value') && _.get(promptData, 'launchConf.ask_limit_on_launch')){
                        schedule.limit = promptData.prompts.limit.templateDefault === promptData.prompts.limit.value ? null : promptData.prompts.limit.value;
                    }
                    if(_.has(promptData, 'prompts.verbosity.value.value') && _.get(promptData, 'launchConf.ask_verbosity_on_launch')){
                        schedule.verbosity = promptData.prompts.verbosity.templateDefault === promptData.prompts.verbosity.value.value ? null : promptData.prompts.verbosity.value.value;
                    }
                    if(_.has(promptData, 'prompts.inventory.value') && _.get(promptData, 'launchConf.ask_inventory_on_launch')){
                        schedule.inventory = promptData.prompts.inventory.templateDefault.id === promptData.prompts.inventory.value.id ? null : promptData.prompts.inventory.value.id;
                    }
                    if(_.has(promptData, 'prompts.diffMode.value') && _.get(promptData, 'launchConf.ask_diff_mode_on_launch')){
                        schedule.diff_mode = promptData.prompts.diffMode.templateDefault === promptData.prompts.diffMode.value ? null : promptData.prompts.diffMode.value;
                    }
                    // Credentials gets POST'd to a separate endpoint
                    // if($scope.promptData.launchConf.ask_credential_on_launch){
                    //     jobLaunchData.credentials = [];
                    //     promptData.credentials.value.forEach((credential) => {
                    //         jobLaunchData.credentials.push(credential.id);
                    //     });
                    // }
                }

                Rest.setUrl(url);
                if (mode === 'add') {
                    Rest.post(schedule)
                        .then(() => {
                            Wait('stop');
                            deferred.resolve();
                        })
                        .catch(({data, status}) => {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'POST to ' + url + ' returned: ' + status });

                            deferred.reject();
                        });
                }
                else {
                    Rest.put(schedule)
                        .then(() => {
                            Wait('stop');
                            deferred.resolve(schedule);
                        })
                        .catch(({data, status}) => {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'POST to ' + url + ' returned: ' + status });

                            deferred.reject();
                        });
                }
            }
            else {
                deferred.reject();
            }

            return deferred.promise;
        };
    }

SchedulePost.$inject =
    [   'Rest',
        'ProcessErrors',
        'RRuleToAPI',
        'Wait',
        '$q'
    ];
