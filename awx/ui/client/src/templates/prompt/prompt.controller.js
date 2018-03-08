export default [ 'Rest', 'GetBasePath', 'ProcessErrors', 'CredentialTypeModel', 'TemplatesStrings',
    function (Rest, GetBasePath, ProcessErrors, CredentialType, strings) {

        // strings.get('deleteResource.HEADER')
        // ${strings.get('deleteResource.CONFIRM', 'template')}

        const vm = this || {};

        vm.strings = strings;

        let scope;
        let modal;

        vm.init = (_scope_) => {
            scope = _scope_;
            ({ modal } = scope[scope.ns]);

            scope.$watch('vm.promptData.triggerModalOpen', () => {
                if(vm.promptData && vm.promptData.triggerModalOpen) {

                    vm.steps = {
                        inventory: {
                            includeStep: false
                        },
                        credential: {
                            includeStep: false
                        },
                        other_prompts: {
                            includeStep: false
                        },
                        survey: {
                            includeStep: false
                        },
                        preview: {
                            includeStep: true,
                            tab: {
                                _active: false,
                                _disabled: true
                            }
                        }
                    };

                    let order = 1;

                    vm.actionText = vm.actionText ? vm.actionText : strings.get('prompt.LAUNCH');

                    vm.forms = {};

                    let credentialType = new CredentialType();

                    credentialType.http.get()
                    .then( (response) => {
                        vm.promptData.prompts.credentials.credentialTypes = {};
                        vm.promptData.prompts.credentials.credentialTypeOptions = [];
                        response.data.results.forEach((credentialTypeRow => {
                            vm.promptData.prompts.credentials.credentialTypes[credentialTypeRow.id] = credentialTypeRow.kind;
                            if(credentialTypeRow.kind.match(/^(cloud|net|ssh|vault)$/)) {
                                if(credentialTypeRow.kind === 'ssh') {
                                    vm.promptData.prompts.credentials.credentialKind = credentialTypeRow.id.toString();
                                }
                                vm.promptData.prompts.credentials.credentialTypeOptions.push({
                                    name: credentialTypeRow.name,
                                    value: credentialTypeRow.id
                                });
                            }
                        }));

                        vm.promptData.prompts.credentials.passwordsNeededToStart = vm.promptData.launchConf.passwords_needed_to_start;
                        vm.promptData.prompts.credentials.passwords = {};

                        vm.promptData.prompts.credentials.value.forEach((credential) => {
                            if (credential.passwords_needed && credential.passwords_needed.length > 0) {
                                credential.passwords_needed.forEach(passwordNeeded => {
                                    let credPassObj = {
                                        id: credential.id,
                                        name: credential.name
                                    };

                                    if(passwordNeeded === "ssh_password") {
                                        vm.promptData.prompts.credentials.passwords.ssh = credPassObj;
                                    }
                                    if(passwordNeeded === "become_password") {
                                        vm.promptData.prompts.credentials.passwords.become = credPassObj;
                                    }
                                    if(passwordNeeded === "ssh_key_unlock") {
                                        vm.promptData.prompts.credentials.passwords.ssh_key_unlock = credPassObj;
                                    }
                                    if(passwordNeeded.startsWith("vault_password")) {
                                        if(passwordNeeded.includes('.')) {
                                            credPassObj.vault_id = passwordNeeded.split(/\.(.+)/)[1];
                                        }

                                        if(!vm.promptData.prompts.credentials.passwords.vault) {
                                            vm.promptData.prompts.credentials.passwords.vault = [];
                                        }

                                        vm.promptData.prompts.credentials.passwords.vault.push(credPassObj);
                                    }
                                });
                            }
                        });

                        vm.promptData.credentialTypeMissing = [];

                        vm.promptData.prompts.variables.ignore = vm.promptData.launchConf.ignore_ask_variables;

                        if(vm.promptData.launchConf.ask_inventory_on_launch) {
                            vm.steps.inventory.includeStep = true;
                            vm.steps.inventory.tab = {
                                _active: true,
                                order: order
                            };
                            order++;
                        }
                        if(vm.promptData.launchConf.ask_credential_on_launch || (vm.promptData.launchConf.passwords_needed_to_start && vm.promptData.launchConf.passwords_needed_to_start.length > 0)) {
                            vm.steps.credential.includeStep = true;
                            vm.steps.credential.tab = {
                                _active: order === 1 ? true : false,
                                _disabled: order === 1 ? false : true,
                                order: order
                            };
                            order++;
                        }
                        if(vm.promptData.launchConf.ask_verbosity_on_launch || vm.promptData.launchConf.ask_job_type_on_launch || vm.promptData.launchConf.ask_limit_on_launch || vm.promptData.launchConf.ask_tags_on_launch || vm.promptData.launchConf.ask_skip_tags_on_launch || (vm.promptData.launchConf.ask_variables_on_launch && !vm.promptData.launchConf.ignore_ask_variables) || vm.promptData.launchConf.ask_diff_mode_on_launch) {
                            vm.steps.other_prompts.includeStep = true;
                            vm.steps.other_prompts.tab = {
                                _active: order === 1 ? true : false,
                                _disabled: order === 1 ? false : true,
                                order: order
                            };
                            order++;
                        }
                        if(vm.promptData.launchConf.survey_enabled) {
                            vm.steps.survey.includeStep = true;
                            vm.steps.survey.tab = {
                                _active: order === 1 ? true : false,
                                _disabled: order === 1 ? false : true,
                                order: order
                            };
                            order++;
                        }
                        vm.steps.preview.tab.order = order;
                        modal.show('PROMPT');
                        vm.promptData.triggerModalOpen = false;
                    })
                    .catch(({data, status}) => {
                        ProcessErrors(scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to get credential types. GET status: ' + status
                        });
                    });
                }
            }, true);
        };

        vm.next = (currentTab) => {
            Object.keys(vm.steps).forEach(step => {
                if(vm.steps[step].tab) {
                    if(vm.steps[step].tab.order === currentTab.order) {
                        vm.steps[step].tab._active = false;
                    } else if(vm.steps[step].tab.order === currentTab.order + 1) {
                        vm.steps[step].tab._active = true;
                        vm.steps[step].tab._disabled = false;
                    }
                }
            });
        };

        vm.finish = () => {
            vm.promptData.triggerModalOpen = false;
            if(vm.onFinish) {
                vm.onFinish();
            }
            modal.hide();
        };

        vm.cancel = () => {
            vm.promptData.triggerModalOpen = false;
            modal.hide();
        };
}];
