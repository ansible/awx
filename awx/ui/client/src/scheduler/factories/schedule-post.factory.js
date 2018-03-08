export default
    function SchedulePost(Rest, ProcessErrors, RRuleToAPI, Wait, $q, Schedule) {
        return function(params) {
            var scope = params.scope,
                url = params.url,
                scheduler = params.scheduler,
                mode = params.mode,
                scheduleData = (params.schedule) ? params.schedule : {},
                promptData = params.promptData,
                priorCredentials = params.priorCredentials ? params.priorCredentials : [],
                newSchedule, rrule, extra_vars;
            const deferred = $q.defer();
            if (scheduler.isValid()) {
                Wait('start');
                newSchedule = scheduler.getValue();
                rrule = scheduler.getRRule();
                scheduleData.name = newSchedule.name;
                scheduleData.rrule = RRuleToAPI(rrule.toString(), scope);
                scheduleData.description = (/error/.test(rrule.toText())) ? '' : rrule.toText();

                if (scope.isFactCleanup) {
                    extra_vars = {
                        "older_than": scope.scheduler_form.keep_amount.$viewValue + scope.scheduler_form.keep_unit.$viewValue.value,
                        "granularity": scope.scheduler_form.granularity_keep_amount.$viewValue + scope.scheduler_form.granularity_keep_unit.$viewValue.value
                    };
                    scheduleData.extra_data = JSON.stringify(extra_vars);
                } else if (scope.cleanupJob) {
                    extra_vars = {
                        "days" : scope.scheduler_form.schedulerPurgeDays.$viewValue
                    };
                    scheduleData.extra_data = JSON.stringify(extra_vars);
                }
                else if(scope.extraVars){
                    scheduleData.extra_data = scope.parseType === 'yaml' ?
                        (scope.extraVars === '---' ? "" : jsyaml.safeLoad(scope.extraVars)) : scope.extraVars;
                }

                if(promptData) {
                    if(promptData.launchConf.survey_enabled){
                        for (var i=0; i < promptData.surveyQuestions.length; i++){
                            var fld = promptData.surveyQuestions[i].variable;
                            // grab all survey questions that have answers
                            if(promptData.surveyQuestions[i].required || (promptData.surveyQuestions[i].required === false && promptData.surveyQuestions[i].model.toString()!=="")) {
                                if(!scheduleData.extra_data) {
                                    scheduleData.extra_data = {};
                                }
                                scheduleData.extra_data[fld] = promptData.surveyQuestions[i].model;
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
                                        scheduleData.extra_data[fld] = "";
                                    }
                                    break;
                                }
                            }
                        }
                    }

                    if(_.has(promptData, 'prompts.jobType.value.value') && _.get(promptData, 'launchConf.ask_job_type_on_launch')) {
                        scheduleData.job_type = promptData.launchConf.defaults.job_type && promptData.launchConf.defaults.job_type === promptData.prompts.jobType.value.value ? null : promptData.prompts.jobType.value.value;
                    }
                    if(_.has(promptData, 'prompts.tags.value') && _.get(promptData, 'launchConf.ask_tags_on_launch')){
                        const templateDefaultJobTags = promptData.launchConf.defaults.job_tags.split(',');
                        scheduleData.job_tags = (_.isEqual(templateDefaultJobTags.sort(), promptData.prompts.tags.value.map(a => a.value).sort())) ? null : promptData.prompts.tags.value.map(a => a.value).join();
                    }
                    if(_.has(promptData, 'prompts.skipTags.value') && _.get(promptData, 'launchConf.ask_skip_tags_on_launch')){
                        const templateDefaultSkipTags = promptData.launchConf.defaults.skip_tags.split(',');
                        scheduleData.skip_tags = (_.isEqual(templateDefaultSkipTags.sort(), promptData.prompts.skipTags.value.map(a => a.value).sort())) ? null : promptData.prompts.skipTags.value.map(a => a.value).join();
                    }
                    if(_.has(promptData, 'prompts.limit.value') && _.get(promptData, 'launchConf.ask_limit_on_launch')){
                        scheduleData.limit = promptData.launchConf.defaults.limit && promptData.launchConf.defaults.limit === promptData.prompts.limit.value ? null : promptData.prompts.limit.value;
                    }
                    if(_.has(promptData, 'prompts.verbosity.value.value') && _.get(promptData, 'launchConf.ask_verbosity_on_launch')){
                        scheduleData.verbosity = promptData.launchConf.defaults.verbosity && promptData.launchConf.defaults.verbosity === promptData.prompts.verbosity.value.value ? null : promptData.prompts.verbosity.value.value;
                    }
                    if(_.has(promptData, 'prompts.inventory.value') && _.get(promptData, 'launchConf.ask_inventory_on_launch')){
                        scheduleData.inventory = promptData.launchConf.defaults.inventory && promptData.launchConf.defaults.inventory.id === promptData.prompts.inventory.value.id ? null : promptData.prompts.inventory.value.id;
                    }
                    if(_.has(promptData, 'prompts.diffMode.value') && _.get(promptData, 'launchConf.ask_diff_mode_on_launch')){
                        scheduleData.diff_mode = promptData.launchConf.defaults.diff_mode && promptData.launchConf.defaults.diff_mode === promptData.prompts.diffMode.value ? null : promptData.prompts.diffMode.value;
                    }
                }

                Rest.setUrl(url);
                if (mode === 'add') {
                    Rest.post(scheduleData)
                        .then(({data}) => {
                            if(_.get(promptData, 'launchConf.ask_credential_on_launch')){
                                // This finds the credentials that were selected in the prompt but don't occur
                                // in the template defaults
                                const credentialsToPost = promptData.prompts.credentials.value.filter(function(credFromPrompt) {
                                    const defaultCreds = promptData.launchConf.defaults.credentials ? promptData.launchConf.defaults.credentials : [];
                                    return !defaultCreds.some(function(defaultCred) {
                                        return credFromPrompt.id === defaultCred.id;
                                    });
                                });

                                const promises = [];
                                const schedule = new Schedule();

                                credentialsToPost.forEach((credentialToPost) => {
                                    promises.push(schedule.postCredential({
                                        id: data.id,
                                        data: {
                                            id: credentialToPost.id
                                        }
                                    }));
                                });

                                $q.all(promises)
                                    .then(() => {
                                        Wait('stop');
                                        deferred.resolve();
                                    });
                            } else {
                                Wait('stop');
                                deferred.resolve();
                            }
                        })
                        .catch(({data, status}) => {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'POST to ' + url + ' returned: ' + status });

                            deferred.reject();
                        });
                }
                else {
                    Rest.put(scheduleData)
                        .then(({data}) => {
                            if(_.get(promptData, 'launchConf.ask_credential_on_launch')){
                                const credentialsNotInPriorCredentials = promptData.prompts.credentials.value.filter(function(credFromPrompt) {
                                    const defaultCreds = promptData.launchConf.defaults.credentials ? promptData.launchConf.defaults.credentials : [];
                                    return !defaultCreds.some(function(defaultCred) {
                                        return credFromPrompt.id === defaultCred.id;
                                    });
                                });

                                const credentialsToAdd = credentialsNotInPriorCredentials.filter(function(credNotInPrior) {
                                    return !priorCredentials.some(function(priorCred) {
                                        return credNotInPrior.id === priorCred.id;
                                    });
                                });

                                const credentialsToRemove = priorCredentials.filter(function(priorCred) {
                                    return !credentialsNotInPriorCredentials.some(function(credNotInPrior) {
                                        return priorCred.id === credNotInPrior.id;
                                    });
                                });

                                const promises = [];
                                const schedule = new Schedule();

                                credentialsToAdd.forEach((credentialToAdd) => {
                                    promises.push(schedule.postCredential({
                                        id: data.id,
                                        data: {
                                            id: credentialToAdd.id
                                        }
                                    }));
                                });

                                credentialsToRemove.forEach((credentialToRemove) => {
                                    promises.push(schedule.postCredential({
                                        id: data.id,
                                        data: {
                                            id: credentialToRemove.id,
                                            disassociate: true
                                        }
                                    }));
                                });

                                $q.all(promises)
                                    .then(() => {
                                        Wait('stop');
                                        deferred.resolve();
                                    });
                            } else {
                                Wait('stop');
                                deferred.resolve();
                            }

                            Wait('stop');
                            deferred.resolve(scheduleData);
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
        '$q',
        'ScheduleModel'
    ];
