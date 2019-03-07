export default [ 'ProcessErrors', 'CredentialTypeModel', 'TemplatesStrings', '$filter',
    function (ProcessErrors, CredentialType, strings, $filter) {

        const vm = this || {};

        vm.strings = strings;

        let scope;
        let modal;

        vm.init = (_scope_) => {
            scope = _scope_;
            ({ modal } = scope[scope.ns]);

            scope.$watch('vm.promptData.triggerModalOpen', () => {
                vm.actionButtonClicked = false;
                if(vm.promptData && vm.promptData.triggerModalOpen) {
                    scope.$emit('launchModalOpen', true);
                    vm.promptDataClone = _.cloneDeep(vm.promptData);

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

                    credentialType.http.get({ params: { page_size: 200 }})
                    .then( (response) => {
                        vm.promptDataClone.prompts.credentials.credentialTypes = {};
                        vm.promptDataClone.prompts.credentials.credentialTypeOptions = [];
                        response.data.results.forEach((credentialTypeRow => {
                            vm.promptDataClone.prompts.credentials.credentialTypes[credentialTypeRow.id] = credentialTypeRow.kind;
                            if(credentialTypeRow.kind.match(/^(cloud|net|ssh|vault)$/)) {
                                if(credentialTypeRow.kind === 'ssh') {
                                    vm.promptDataClone.prompts.credentials.credentialKind = credentialTypeRow.id.toString();
                                }
                                vm.promptDataClone.prompts.credentials.credentialTypeOptions.push({
                                    name: credentialTypeRow.name,
                                    value: credentialTypeRow.id
                                });
                            }
                        }));

                        vm.promptDataClone.prompts.credentials.passwords = {};

                        vm.promptDataClone.prompts.credentials.value.forEach((credential) => {
                            if(credential.inputs) {
                                if(credential.inputs.password && credential.inputs.password === "ASK") {
                                    vm.promptDataClone.prompts.credentials.passwords.ssh_password = {
                                        id: credential.id,
                                        name: credential.name
                                    };
                                }
                                if(credential.inputs.become_password && credential.inputs.become_password === "ASK") {
                                    vm.promptDataClone.prompts.credentials.passwords.become_password = {
                                        id: credential.id,
                                        name: credential.name
                                    };
                                }
                                if(credential.inputs.ssh_key_unlock && credential.inputs.ssh_key_unlock === "ASK") {
                                    vm.promptDataClone.prompts.credentials.passwords.ssh_key_unlock = {
                                        id: credential.id,
                                        name: credential.name
                                    };
                                }
                                if(credential.inputs.vault_password && credential.inputs.vault_password === "ASK") {
                                    if(!vm.promptDataClone.prompts.credentials.passwords.vault) {
                                        vm.promptDataClone.prompts.credentials.passwords.vault = [];
                                    }
                                    vm.promptDataClone.prompts.credentials.passwords.vault.push({
                                        id: credential.id,
                                        name: credential.name,
                                        vault_id: credential.inputs.vault_id
                                    });
                                }
                            } else if(credential.passwords_needed && credential.passwords_needed.length > 0) {
                                credential.passwords_needed.forEach((passwordNeeded) => {
                                    if (passwordNeeded === "ssh_password" ||
                                        passwordNeeded === "become_password" ||
                                        passwordNeeded === "ssh_key_unlock"
                                    ) {
                                        vm.promptDataClone.prompts.credentials.passwords[passwordNeeded] = {
                                            id: credential.id,
                                            name: credential.name
                                        };
                                    } else if (passwordNeeded.startsWith("vault_password")) {
                                        let vault_id = null;
                                        if (passwordNeeded.includes('.')) {
                                            vault_id = passwordNeeded.split(/\.(.+)/)[1];
                                        }

                                        if (!vm.promptDataClone.prompts.credentials.passwords.vault) {
                                            vm.promptDataClone.prompts.credentials.passwords.vault = [];
                                        }

                                        vm.promptDataClone.prompts.credentials.passwords.vault.push({
                                            id: credential.id,
                                            name: credential.name,
                                            vault_id: vault_id
                                        });
                                    }
                                });
                            }
                        });

                        vm.promptDataClone.credentialTypeMissing = [];

                        vm.promptDataClone.prompts.variables.ignore = vm.promptDataClone.launchConf.ignore_ask_variables;

                        if(vm.promptDataClone.launchConf.ask_inventory_on_launch) {
                            vm.steps.inventory.includeStep = true;
                            vm.steps.inventory.tab = {
                                _active: true,
                                order: order
                            };
                            order++;
                        }
                        if (vm.promptDataClone.launchConf.ask_credential_on_launch ||
                            (_.has(vm, 'promptDataClone.prompts.credentials.passwords.vault') &&
                            vm.promptDataClone.prompts.credentials.passwords.vault.length > 0) ||
                            _.has(vm, 'promptDataClone.prompts.credentials.passwords.ssh_key_unlock') ||
                            _.has(vm, 'promptDataClone.prompts.credentials.passwords.become_password') ||
                            _.has(vm, 'promptDataClone.prompts.credentials.passwords.ssh_password')
                        ) {
                            vm.steps.credential.includeStep = true;
                            vm.steps.credential.tab = {
                                _active: order === 1 ? true : false,
                                _disabled: (order === 1 || vm.readOnlyPrompts) ? false : true,
                                order: order
                            };
                            order++;
                        }
                        if(vm.promptDataClone.launchConf.ask_verbosity_on_launch || vm.promptDataClone.launchConf.ask_job_type_on_launch || vm.promptDataClone.launchConf.ask_limit_on_launch || vm.promptDataClone.launchConf.ask_tags_on_launch || vm.promptDataClone.launchConf.ask_skip_tags_on_launch || (vm.promptDataClone.launchConf.ask_variables_on_launch && !vm.promptDataClone.launchConf.ignore_ask_variables) || vm.promptDataClone.launchConf.ask_diff_mode_on_launch) {
                            vm.steps.other_prompts.includeStep = true;
                            vm.steps.other_prompts.tab = {
                                _active: order === 1 ? true : false,
                                _disabled: (order === 1 || vm.readOnlyPrompts) ? false : true,
                                order: order
                            };
                            order++;

                            let codemirror = () =>  {
                                return {
                                    validate:{}
                                };
                            };
                            vm.codeMirror = new codemirror();
                        }
                        if(vm.promptDataClone.launchConf.survey_enabled) {
                            vm.steps.survey.includeStep = true;
                            vm.steps.survey.tab = {
                                _active: order === 1 ? true : false,
                                _disabled: (order === 1 || vm.readOnlyPrompts) ? false : true,
                                order: order
                            };
                            order++;
                        }
                        vm.steps.preview.tab.order = order;
                        vm.steps.preview.tab._disabled = vm.readOnlyPrompts ? false : true;
                        modal.show($filter('sanitize')(vm.promptDataClone.templateName));
                        vm.promptData.triggerModalOpen = false;

                        modal.onClose = () => {
                            scope.$emit('launchModalOpen', false);
                        };
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
            if(_.has(vm, 'steps.other_prompts.tab._active') && vm.steps.other_prompts.tab._active === true){
                try {
                    if (vm.codeMirror.validate) {
                        vm.codeMirror.validate();
                    }
                } catch (err) {
                    event.preventDefault();
                    return;
                }
            }
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
            // Disable the action button to prevent double clicking
            vm.actionButtonClicked = true;

            _.forEach(vm.promptDataClone, (value, key) => {
                vm.promptData[key] = value;
            });

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
