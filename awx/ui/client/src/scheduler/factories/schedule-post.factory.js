export default
    function SchedulePost(Rest, ProcessErrors, RRuleToAPI, Wait, $q, Schedule, PromptService) {
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

                if (scope.askDaysToKeep) {
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
                    scheduleData = PromptService.bundlePromptDataForSaving({
                        promptData: promptData,
                        dataToSave: scheduleData
                    });
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
        'ScheduleModel',
        'PromptService'
    ];
