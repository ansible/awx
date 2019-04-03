/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    ['ParseTypeChange', 'CreateSelect2', 'TemplatesStrings', '$timeout', 'ToJSON', function(ParseTypeChange, CreateSelect2, strings, $timeout, ToJSON) {
            const vm = this;

            vm.strings = strings;

            let scope;

            vm.init = (_scope_, controller, el) => {
                scope = _scope_;

                scope.parseType = 'yaml';

                // Can't pass otherPrompts.variables.value into ParseTypeChange
                // due to the fact that Angular CodeMirror uses scope[string]
                // notation.
                scope.extraVariables = scope.promptData.prompts.variables.value;

                scope.$watch('extraVariables', () => {
                    scope.promptData.prompts.variables.value = scope.extraVariables;
                });

                let codemirrorExtraVars = () => {
                    if(scope.promptData.launchConf.ask_variables_on_launch && !scope.promptData.prompts.variables.ignore) {
                        $timeout(() => {
                            ParseTypeChange({
                                scope: scope,
                                variable: 'extraVariables',
                                field_id: 'job_launch_variables'
                            });
                        });
                    }
                };

                if(scope.promptData.launchConf.ask_job_type_on_launch) {
                    CreateSelect2({
                        element: '#job_launch_job_type',
                        multiple: false
                    });
                }

                if(scope.promptData.launchConf.ask_verbosity_on_launch) {
                    CreateSelect2({
                        element: '#job_launch_verbosity',
                        multiple: false
                    });
                }

                if(scope.promptData.launchConf.ask_tags_on_launch) {
                    // Ensure that the options match the currently selected tags.  These two things
                    // might get out of sync if the user re-opens the prompts before saving the
                    // schedule/wf node
                    scope.promptData.prompts.tags.options = _.map(scope.promptData.prompts.tags.value, function(tag){
                        return {
                            value: tag.value,
                            name: tag.name,
                            label: tag.label
                        };
                    });
                    CreateSelect2({
                        element: '#job_launch_job_tags',
                        multiple: true,
                        addNew: true
                    });
                }

                if(scope.promptData.launchConf.ask_skip_tags_on_launch) {
                    // Ensure that the options match the currently selected tags.  These two things
                    // might get out of sync if the user re-opens the prompts before saving the
                    // schedule/wf node
                    scope.promptData.prompts.skipTags.options = _.map(scope.promptData.prompts.skipTags.value, function(tag){
                        return {
                            value: tag.value,
                            name: tag.name,
                            label: tag.label
                        };
                    });
                    CreateSelect2({
                        element: '#job_launch_skip_tags',
                        multiple: true,
                        addNew: true
                    });
                }

                if(scope.isActiveStep) {
                    codemirrorExtraVars();
                }

                scope.$watch('isActiveStep', () => {
                    if(scope.isActiveStep) {
                        codemirrorExtraVars();
                    }
                });

                function validate () {
                    return ToJSON(scope.parseType, scope.extraVariables, true);
                }
                scope.validate = validate;

                function focusFirstInput () {
                  const inputs = el.find('input[type=text], select, textarea:visible, .CodeMirror textarea');
                  if (inputs.length) {
                    inputs.get(0).focus();
                  }
                }

                angular.element(el).ready(() => {
                    focusFirstInput();
                });

                scope.$on('promptTabChange', (event, args) => {
                    if (args.step === 'other_prompts') {
                        angular.element(el).ready(() => {
                          focusFirstInput();
                        });
                    }
                });
            };

            vm.toggleDiff = () => {
                scope.promptData.prompts.diffMode.value = !scope.promptData.prompts.diffMode.value;
            };

            vm.updateParseType = (parseType) => {
                scope.parseType = parseType;
                // This function gets added to scope by the ParseTypeChange factory
                scope.parseTypeChange('parseType', 'extraVariables');
            };
        }
    ];
