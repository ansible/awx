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

                vm.actionButtonClicked = false;
                if(vm.promptData && vm.promptData.triggerModalOpen) {

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

                    credentialType.http.get()
                    .then( (response) => {
                        vm.promptDataClone.prompts.credentials.credentialTypes = {};
                        vm.promptDataClone.prompts.credentials.credentialTypeOptions = [];
                        let machineCredTypeId = null;
                        response.data.results.forEach((credentialTypeRow => {
                            vm.promptDataClone.prompts.credentials.credentialTypes[credentialTypeRow.id] = credentialTypeRow.kind;
                            if(credentialTypeRow.kind.match(/^(cloud|net|ssh|vault)$/)) {
                                if(credentialTypeRow.kind === 'ssh') {
                                    machineCredTypeId = credentialTypeRow.id;
                                    vm.promptDataClone.prompts.credentials.credentialKind = credentialTypeRow.id.toString();
                                }
                                vm.promptDataClone.prompts.credentials.credentialTypeOptions.push({
                                    name: credentialTypeRow.name,
                                    value: credentialTypeRow.id
                                });
                            }
                        }));

                        vm.promptDataClone.prompts.credentials.passwords = {};

                        if(vm.promptDataClone.launchConf.passwords_needed_to_start) {
                            let machineCredPassObj = null;
                            vm.promptDataClone.launchConf.passwords_needed_to_start.forEach((passwordNeeded) => {
                                if (passwordNeeded === "ssh_password" ||
                                    passwordNeeded === "become_password" ||
                                    passwordNeeded === "ssh_key_unlock"
                                ) {
                                    if (!machineCredPassObj) {
                                        vm.promptDataClone.prompts.credentials.value.forEach((defaultCredential) => {
                                            if (defaultCredential.kind && defaultCredential.kind === "ssh") {
                                                machineCredPassObj = {
                                                    id: defaultCredential.id,
                                                    name: defaultCredential.name
                                                };
                                            } else if (defaultCredential.passwords_needed) {
                                                defaultCredential.passwords_needed.forEach((neededPassword) => {
                                                    if (neededPassword === passwordNeeded) {
                                                        machineCredPassObj = {
                                                            id: defaultCredential.id,
                                                            name: defaultCredential.name
                                                        };
                                                    }
                                                });
                                            }
                                        });
                                    }

                                    vm.promptDataClone.prompts.credentials.passwords[passwordNeeded] = angular.copy(machineCredPassObj);
                                } else if (passwordNeeded.startsWith("vault_password")) {
                                    let vault_id = null;
                                    if (passwordNeeded.includes('.')) {
                                        vault_id = passwordNeeded.split(/\.(.+)/)[1];
                                    }

                                    if (!vm.promptDataClone.prompts.credentials.passwords.vault) {
                                        vm.promptDataClone.prompts.credentials.passwords.vault = [];
                                    }

                                    // Loop across the default credentials to find the name of the
                                    // credential that requires a password
                                    vm.promptDataClone.prompts.credentials.value.forEach((defaultCredential) => {
                                        if (vm.promptDataClone.prompts.credentials.credentialTypes[defaultCredential.credential_type] === "vault") {
                                            let defaultCredVaultId = defaultCredential.vault_id || _.get(defaultCredential, 'inputs.vault_id') || null;
                                            if (defaultCredVaultId === vault_id) {
                                                vm.promptDataClone.prompts.credentials.passwords.vault.push({
                                                    id: defaultCredential.id,
                                                    name: defaultCredential.name,
                                                    vault_id: defaultCredVaultId
                                                });
                                            }
                                        }
                                    });
                                }
                            });
                        }

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
                        if(vm.promptDataClone.launchConf.ask_credential_on_launch || (vm.promptDataClone.launchConf.passwords_needed_to_start && vm.promptDataClone.launchConf.passwords_needed_to_start.length > 0)) {
                            vm.steps.credential.includeStep = true;
                            vm.steps.credential.tab = {
                                _active: order === 1 ? true : false,
                                _disabled: order === 1 ? false : true,
                                order: order
                            };
                            order++;
                        }
                        if(vm.promptDataClone.launchConf.ask_verbosity_on_launch || vm.promptDataClone.launchConf.ask_job_type_on_launch || vm.promptDataClone.launchConf.ask_limit_on_launch || vm.promptDataClone.launchConf.ask_tags_on_launch || vm.promptDataClone.launchConf.ask_skip_tags_on_launch || (vm.promptDataClone.launchConf.ask_variables_on_launch && !vm.promptDataClone.launchConf.ignore_ask_variables) || vm.promptDataClone.launchConf.ask_diff_mode_on_launch) {
                            vm.steps.other_prompts.includeStep = true;
                            vm.steps.other_prompts.tab = {
                                _active: order === 1 ? true : false,
                                _disabled: order === 1 ? false : true,
                                order: order
                            };
                            order++;
                        }
                        if(vm.promptDataClone.launchConf.survey_enabled) {
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

                        modal.onClose = () => {
                            scope.$emit('launchModalOpen', false);
                        };

                        scope.$emit('launchModalOpen', true);
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
