/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    ['ParseTypeChange', 'CreateSelect2', 'TemplatesStrings', '$timeout', function(ParseTypeChange, CreateSelect2, strings, $timeout) {
            const vm = this;

            vm.strings = strings;

            let scope;
            let launch;

            vm.init = (_scope_, _launch_) => {
                scope = _scope_;
                launch = _launch_;

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
                    CreateSelect2({
                        element: '#job_launch_job_tags',
                        multiple: true,
                        addNew: true
                    });
                }

                if(scope.promptData.launchConf.ask_skip_tags_on_launch) {
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
