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
            let launch;

            let consolidateTags = (tagModel, tagId) => {
                let tags = angular.copy(tagModel);
                $(tagId).siblings(".select2").first().find(".select2-selection__choice").each((optionIndex, option) => {
                    tags.push({
                        value: option.title,
                        name: option.title,
                        label: option.title
                    });
                });

                return [...tags.reduce((map, tag) => map.has(tag.value) ? map : map.set(tag.value, tag), new Map()).values()];
            };

            vm.init = (_scope_, _launch_) => {
                scope = _scope_;
                launch = _launch_;

                vm.showJobTags = true;
                vm.showSkipTags = true;

                scope.parseType = 'yaml';

                scope.promptData.extraVars = ToJSON(scope.parseType, scope.promptData.prompts.variables.value, false);

                if(scope.promptData.launchConf.ask_tags_on_launch) {
                    scope.promptData.prompts.tags.value = consolidateTags(scope.promptData.prompts.tags.value, "#job_launch_job_tags");
                }

                if(scope.promptData.launchConf.ask_skip_tags_on_launch) {
                    scope.promptData.prompts.skipTags.value = consolidateTags(scope.promptData.prompts.skipTags.value, "#job_launch_skip_tags");
                }

                if(scope.promptData.launchConf.survey_enabled){
                    scope.promptData.surveyQuestions.forEach(surveyQuestion => {
                        // grab all survey questions that have answers
                        if(surveyQuestion.required || (surveyQuestion.required === false && surveyQuestion.model.toString()!=="")) {
                            if(!scope.promptData.extraVars) {
                                scope.promptData.extraVars = {};
                            }
                            scope.promptData.extraVars[surveyQuestion.variable] = surveyQuestion.model;
                        }

                        if(surveyQuestion.required === false && _.isEmpty(surveyQuestion.model)) {
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
                    });
                }

                scope.promptExtraVars = $.isEmptyObject(scope.promptData.extraVars) ? '---' : jsyaml.safeDump(scope.promptData.extraVars);

                ParseTypeChange({
                    scope: scope,
                    variable: 'promptExtraVars',
                    field_id: 'job_launch_preview_variables',
                    readOnly: true
                });
            };
        }
    ];
