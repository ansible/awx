/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [ 'ParseTypeChange', 'ToJSON', 'TemplatesStrings', function(ParseTypeChange, ToJSON, strings) {
            const vm = this;

            vm.strings = strings;

            let scope;

            vm.init = (_scope_) => {
                scope = _scope_;

                vm.showJobTags = true;
                vm.showSkipTags = true;

                scope.parseType = 'yaml';

                const surveyPasswords = {};

                if (scope.promptData.launchConf.survey_enabled){
                    scope.promptData.extraVars = ToJSON(scope.parseType, scope.promptData.prompts.variables.value, false);
                    scope.promptData.surveyQuestions.forEach(surveyQuestion => {
                        if (!scope.promptData.extraVars) {
                            scope.promptData.extraVars = {};
                        }
                        // grab all survey questions that have answers
                        if (surveyQuestion.required || (surveyQuestion.required === false && surveyQuestion.model.toString()!=="")) {
                            scope.promptData.extraVars[surveyQuestion.variable] = surveyQuestion.model;
                        }

                        if (surveyQuestion.required === false && _.isEmpty(surveyQuestion.model)) {
                            switch (surveyQuestion.type) {
                                // for optional text and text-areas, submit a blank string if min length is 0
                                // -- this is confusing, for an explanation see:
                                //    http://docs.ansible.com/ansible-tower/latest/html/userguide/job_templates.html#optional-survey-questions
                                //
                                case "text":
                                case "textarea":
                                if (surveyQuestion.min === 0) {
                                    scope.promptData.extraVars[surveyQuestion.variable] = "";
                                }
                                break;
                            }
                        }

                        if (surveyQuestion.type === 'password' && surveyQuestion.model.toString()!=="") {
                            surveyPasswords[surveyQuestion.variable] = '$encrypted$';
                        }
                    });
                    // We don't want to modify the extra vars when we merge them with the survey
                    // password $encrypted$ strings so we clone it
                    const extraVarsClone = _.cloneDeep(scope.promptData.extraVars);
                    // Replace the survey passwords with $encrypted$ to display to the user
                    const cleansedExtraVars = extraVarsClone ? Object.assign(extraVarsClone, surveyPasswords) : {};

                    scope.promptExtraVars = $.isEmptyObject(scope.promptData.extraVars) ? '---' : '---\n' + jsyaml.safeDump(cleansedExtraVars);
                } else {
                    scope.promptData.extraVars = scope.promptData.prompts.variables.value;
                    scope.promptExtraVars = scope.promptData.prompts.variables.value && scope.promptData.prompts.variables.value !== '' ? scope.promptData.prompts.variables.value : '---\n';
                }

                ParseTypeChange({
                    scope: scope,
                    variable: 'promptExtraVars',
                    field_id: 'job_launch_preview_variables',
                    readOnly: true
                });
            };
        }
    ];
