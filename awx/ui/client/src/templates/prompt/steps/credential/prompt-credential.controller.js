/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   'CredentialList', 'QuerySet', 'GetBasePath', 'CreateSelect2', 'TemplatesStrings',
        function(CredentialList, qs, GetBasePath, CreateSelect2, strings) {
            const vm = this;

            vm.strings = strings;

            let scope;
            let launch;

            let updateSelectedRow = () => {
                if(scope.credentials && scope.credentials.length > 0) {
                    scope.credentials.forEach((credential, i) => {
                        scope.credentials[i].checked = 0;
                    });
                    scope.promptData.prompts.credentials.value.forEach((selectedCredential) => {
                        if(selectedCredential.credential_type === parseInt(scope.promptData.prompts.credentials.credentialKind)) {
                            scope.credentials.forEach((credential, i) => {
                                if(scope.credentials[i].id === selectedCredential.id) {
                                    scope.credentials[i].checked = 1;
                                }
                            });
                        }
                    });
                }
            };

            let wipePasswords = (cred) => {
                if(cred.passwords_needed) {
                    cred.passwords_needed.forEach((passwordNeeded => {
                        if(passwordNeeded === 'ssh_password') {
                            delete scope.promptData.prompts.credentials.passwords.ssh;
                        } else if(passwordNeeded === 'become_password') {
                            delete scope.promptData.prompts.credentials.passwords.become;
                        } else if(passwordNeeded === 'ssh_key_unlock') {
                            delete scope.promptData.prompts.credentials.passwords.ssh_key_unlock;
                        } else if(passwordNeeded.startsWith("vault_password")) {
                            for (let i = scope.promptData.prompts.credentials.passwords.vault.length - 1; i >= 0; i--) {
                                if(cred.id === scope.promptData.prompts.credentials.passwords.vault[i].id) {
                                    scope.promptData.prompts.credentials.passwords.vault.splice(i, 1);
                                }
                            }
                        }
                    }));
                } else if(cred.inputs && !_.isEmpty(cred.inputs)) {
                    if(cred.inputs.password && cred.inputs.password === "ASK") {
                        delete scope.promptData.prompts.credentials.passwords.ssh;
                    } else if(cred.inputs.become_password && cred.inputs.become_password === "ASK") {
                        delete scope.promptData.prompts.credentials.passwords.become;
                    } else if(cred.inputs.ssh_key_unlock && cred.inputs.ssh_key_unlock === "ASK") {
                        delete scope.promptData.prompts.credentials.passwords.ssh_key_unlock;
                    } else if(cred.inputs.vault_password && cred.inputs.vault_password === "ASK") {
                        for (let i = scope.promptData.prompts.credentials.passwords.vault.length - 1; i >= 0; i--) {
                            if(cred.id === scope.promptData.prompts.credentials.passwords.vault[i].id) {
                                scope.promptData.prompts.credentials.passwords.vault.splice(i, 1);
                            }
                        }
                    }
                }

            };

            let updateNeededPasswords = (cred) => {
                if(cred.inputs) {
                    let credPassObj = {
                        id: cred.id,
                        name: cred.name
                    };
                    if(cred.inputs.password && cred.inputs.password === "ASK") {
                        scope.promptData.prompts.credentials.passwords.ssh = credPassObj;
                    } else if(cred.inputs.become_password && cred.inputs.become_password === "ASK") {
                        scope.promptData.prompts.credentials.passwords.become = credPassObj;
                    } else if(cred.inputs.ssh_key_unlock && cred.inputs.ssh_key_unlock === "ASK") {
                        scope.promptData.prompts.credentials.passwords.ssh_key_unlock = credPassObj;
                    } else if(cred.inputs.vault_password && cred.inputs.vault_password === "ASK") {
                        credPassObj.vault_id = cred.inputs.vault_id;
                        if(!scope.promptData.prompts.credentials.passwords.vault) {
                            scope.promptData.prompts.credentials.passwords.vault = [];
                        }
                        scope.promptData.prompts.credentials.passwords.vault.push(credPassObj);
                    }
                }
            };

            vm.init = (_scope_, _launch_) => {
                scope = _scope_;
                launch = _launch_;

                scope.toggle_row = (selectedRow) => {
                    for (let i = scope.promptData.prompts.credentials.value.length - 1; i >= 0; i--) {
                        if(scope.promptData.prompts.credentials.value[i].credential_type === parseInt(scope.promptData.prompts.credentials.credentialKind)) {
                            wipePasswords(scope.promptData.prompts.credentials.value[i]);
                            scope.promptData.prompts.credentials.value.splice(i, 1);
                        }
                    }

                    scope.promptData.prompts.credentials.value.push(_.cloneDeep(selectedRow));
                    updateNeededPasswords(selectedRow);
                };

                scope.toggle_credential = (cred) => {
                    // This is a checkbox click.  At the time of writing this the only
                    // multi-select credentials on launch are vault credentials so this
                    // logic should only get executed when a vault credential checkbox
                    // is clicked.

                    let uncheck = false;

                    let removeCredential = (credentialToRemove, index) => {
                        wipePasswords(credentialToRemove);
                        scope.promptData.prompts.credentials.value.splice(index, 1);
                    };

                    // Only one vault credential per vault_id is allowed so we need to check
                    // to see if one has already been selected and if so replace it.
                    for (let i = scope.promptData.prompts.credentials.value.length - 1; i >= 0; i--) {
                        if(cred.credential_type === scope.promptData.prompts.credentials.value[i].credential_type) {
                            if(scope.promptData.prompts.credentials.value[i].id === cred.id) {
                                removeCredential(scope.promptData.prompts.credentials.value[i], i);
                                i = -1;
                                uncheck = true;
                            }
                            else if(scope.promptData.prompts.credentials.value[i].inputs) {
                                if(cred.inputs.vault_id === scope.promptData.prompts.credentials.value[i].inputs.vault_id) {
                                    removeCredential(scope.promptData.prompts.credentials.value[i], i);
                                }
                            } else if(scope.promptData.prompts.credentials.value[i].vault_id) {
                                if(cred.inputs.vault_id === scope.promptData.prompts.credentials.value[i].vault_id) {
                                    removeCredential(scope.promptData.prompts.credentials.value[i], i);
                                }
                            } else {
                                // The currently selected vault credential does not have a vault_id
                                if(!cred.inputs.vault_id || cred.inputs.vault_id === "") {
                                    removeCredential(scope.promptData.prompts.credentials.value[i], i);
                                }
                            }
                        }
                    }

                    if(!uncheck) {
                        scope.promptData.prompts.credentials.value.push(cred);
                        updateNeededPasswords(cred);
                    }
                };

                scope.credential_dataset = [];
                scope.credentials = [];

                let credList = _.cloneDeep(CredentialList);
                credList.emptyListText = strings.get('prompt.NO_CREDS_MATCHING_TYPE');
                scope.list = credList;
                scope.generateCredentialList(scope.promptData.prompts.credentials.credentialKind);

                scope.credential_default_params = {
                    order_by: 'name',
                    page_size: 5
                };

                scope.credential_queryset = {
                    order_by: 'name',
                    page_size: 5
                };

                scope.$watch('promptData.prompts.credentials.credentialKind', (oldKind, newKind) => {
                    if (scope.promptData.prompts.credentials && scope.promptData.prompts.credentials.credentialKind) {
                        if(scope.promptData.prompts.credentials.credentialTypes[oldKind] === "vault" || scope.promptData.prompts.credentials.credentialTypes[newKind] === "vault") {
                            scope.generateCredentialList(scope.promptData.prompts.credentials.credentialKind);
                        }
                        scope.credential_queryset.page = 1;
                        scope.credential_default_params.credential_type = scope.credential_queryset.credential_type = parseInt(scope.promptData.prompts.credentials.credentialKind);

                        qs.search(GetBasePath('credentials'), scope.credential_default_params)
                            .then(res => {
                                scope.credential_dataset = res.data;
                                scope.credentials = scope.credential_dataset.results;
                            });
                    }
                });

                scope.$watchCollection('promptData.prompts.credentials.value', () => {
                    updateSelectedRow();
                });

                scope.$watchCollection('credentials', () => {
                    updateSelectedRow();
                });

                CreateSelect2({
                    element: '#launch-kind-select',
                    multiple: false
                });
            };

            vm.deleteSelectedCredential = (credentialToDelete) => {
                for (let i = scope.promptData.prompts.credentials.value.length - 1; i >= 0; i--) {
                    if(scope.promptData.prompts.credentials.value[i].id === credentialToDelete.id) {
                        wipePasswords(credentialToDelete);
                        scope.promptData.prompts.credentials.value.splice(i, 1);
                    }
                }

                scope.credentials.forEach((credential, i) => {
                    if(credential.id === credentialToDelete.id) {
                        scope.credentials[i].checked = 0;
                    }
                });
            };

            vm.revert = () => {
                scope.promptData.prompts.credentials.value = scope.promptData.prompts.credentials.templateDefault;
                scope.promptData.prompts.credentials.passwords = {
                    vault: []
                };
                scope.promptData.prompts.credentials.value.forEach((credential) => {
                    if (credential.passwords_needed && credential.passwords_needed.length > 0) {
                        credential.passwords_needed.forEach(passwordNeeded => {
                            let credPassObj = {
                                id: credential.id,
                                name: credential.name
                            };

                            if(passwordNeeded === "ssh_password") {
                                scope.promptData.prompts.credentials.passwords.ssh = credPassObj;
                            }
                            if(passwordNeeded === "become_password") {
                                scope.promptData.prompts.credentials.passwords.become = credPassObj;
                            }
                            if(passwordNeeded === "ssh_key_unlock") {
                                scope.promptData.prompts.credentials.passwords.ssh_key_unlock = credPassObj;
                            }
                            if(passwordNeeded.startsWith("vault_password")) {
                                credPassObj.vault_id = credential.vault_id;
                                scope.promptData.prompts.credentials.passwords.vault.push(credPassObj);
                            }
                        });

                    }
                });
            };

            vm.showRevertCredentials = () => {
                if(scope.promptData.launchConf.ask_credential_on_launch) {
                    if(scope.promptData.prompts.credentials.value && scope.promptData.prompts.credentials.templateDefault && (scope.promptData.prompts.credentials.value.length === scope.promptData.prompts.credentials.templateDefault.length)) {
                        let selectedIds = scope.promptData.prompts.credentials.value.map((x) => { return x.id; }).sort();
                        let defaultIds = scope.promptData.prompts.credentials.templateDefault.map((x) => { return x.id; }).sort();
                        return !selectedIds.every((e, i) => { return defaultIds.indexOf(e) === i; });
                    } else {
                        return true;
                    }
                } else {
                    return false;
                }
            };

            vm.togglePassword = (id) => {
                var buttonId = id + "_show_input_button",
                inputId = id;
                if ($(inputId).attr("type") === "password") {
                    $(buttonId).html(strings.get('HIDE'));
                    $(inputId).attr("type", "text");
                } else {
                    $(buttonId).html(strings.get('SHOW'));
                    $(inputId).attr("type", "password");
                }
            };
        }
    ];
