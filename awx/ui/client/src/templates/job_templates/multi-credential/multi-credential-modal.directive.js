export default ['templateUrl', 'Rest', 'GetBasePath', 'generateList', '$compile', 'CreateSelect2', 'i18n', 'MultiCredentialService', 'credentialTypesLookup',
    function(templateUrl, Rest, GetBasePath, GenerateList, $compile, CreateSelect2, i18n, MultiCredentialService, credentialTypesLookup) {
    return {
        restrict: 'E',
        scope: {
            credentialsToPost: '=',
            credentials: '=',
            selectedCredentials: '='
        },
        templateUrl: templateUrl('templates/job_templates/multi-credential/multi-credential-modal'),

        link: function(scope, element) {
            credentialTypesLookup()
                .then(kinds => {
                    scope.credentialKinds = kinds;

                    scope.credentialKind = scope.selectedCredentials.machine && scope.selectedCredentials.machine.readOnly ? (scope.selectedCredentials.vault && scope.selectedCredentials.vault.readOnly ? "" + kinds.Network : "" + kinds.Vault) : "" + kinds.Machine;

                    scope.showModal = function() {
                        $('#multi-credential-modal').modal('show');
                    };

                    scope.destroyModal = function() {
                        scope.credentialKind = kinds.Machine;
                        $('#multi-credential-modal').modal('hide');
                    };

                    scope.generateCredentialList = function() {
                        let html = GenerateList.build({
                            list: scope.list,
                            input_type: 'radio',
                            mode: 'lookup'
                        });
                        $('#multi-credential-modal-body')
                            .append($compile(html)(scope));
                    };

                    $('#multi-credential-modal').on('hidden.bs.modal', function () {
                        $('#multi-credential-modal').off('hidden.bs.modal');
                        $(element).remove();
                    });

                    CreateSelect2({
                        element: `#multi-credential-kind-select`,
                        multiple: false,
                        placeholder: i18n._('Select a credential')
                    });

                    MultiCredentialService.getCredentialTypes()
                        .then(({credential_types, credentialTypeOptions}) => {
                            scope.credential_types = credential_types;
                            scope.credentialTypeOptions = credentialTypeOptions;
                            scope.allCredentialTypeOptions = _.cloneDeep(credentialTypeOptions);

                            // We want to hide machine and vault dropdown options if a credential
                            // has already been selected for those types and the user interacting
                            // with the form doesn't have the ability to change them
                            for(let i=scope.credentialTypeOptions.length - 1; i >=0; i--) {
                                if((scope.selectedCredentials.machine &&
                                    scope.selectedCredentials.machine.credential_type_id === scope.credentialTypeOptions[i].value &&
                                    scope.selectedCredentials.machine.readOnly) ||
                                    (scope.selectedCredentials.vault &&
                                    scope.selectedCredentials.vault.credential_type_id === scope.credentialTypeOptions[i].value &&
                                    scope.selectedCredentials.vault.readOnly)) {
                                        scope.credentialTypeOptions.splice(i, 1);
                                }
                            }

                            scope.$emit('multiCredentialModalLinked');
                        });
                });
        },

        controller: ['$scope', 'CredentialList', 'i18n', 'QuerySet',
            'GetBasePath', function($scope, CredentialList, i18n, qs,
            GetBasePath) {
            let updateExtraCredentialsList = function() {
                let extraCredIds = $scope.selectedCredentials.extra
                    .map(cred => cred.id);
                $scope.credentials.forEach(cred => {
                    if (cred.credential_type !== $scope.credentialKinds.Machine) {
                        cred.checked = (extraCredIds
                            .indexOf(cred.id) > - 1) ? 1 : 0;
                    }
                });

                $scope.credTags = MultiCredentialService
                    .updateCredentialTags($scope.selectedCredentials,
                        $scope.allCredentialTypeOptions);
            };

            let updateMachineCredentialList = function() {
                $scope.credentials.forEach(cred => {
                    if (cred.credential_type === $scope.credentialKinds.Machine) {
                        cred.checked = ($scope.selectedCredentials
                            .machine !== null &&
                            cred.id === $scope.selectedCredentials
                                .machine.id) ? 1 : 0;
                    }
                });

                $scope.credTags = MultiCredentialService
                    .updateCredentialTags($scope.selectedCredentials,
                        $scope.allCredentialTypeOptions);
            };

            let updateVaultCredentialList = function() {
                $scope.credentials.forEach(cred => {
                    if (cred.credential_type === $scope.credentialKinds.Vault) {
                        cred.checked = ($scope.selectedCredentials
                            .vault !== null &&
                            cred.id === $scope.selectedCredentials
                                .vault.id) ? 1 : 0;
                    }
                });

                $scope.credTags = MultiCredentialService
                    .updateCredentialTags($scope.selectedCredentials,
                        $scope.allCredentialTypeOptions);
            };

            let uncheckAllCredentials = function() {
                $scope.credentials.forEach(cred => {
                    cred.checked = 0;
                });

                $scope.credTags = MultiCredentialService
                    .updateCredentialTags($scope.selectedCredentials,
                        $scope.allCredentialTypeOptions);
            };

            let init = function() {
                $scope.originalSelectedCredentials = _.cloneDeep($scope
                    .selectedCredentials);
                $scope.credential_dataset = [];
                $scope.credentials = $scope.credentials || [];
                $scope.listRendered = false;

                let credList = _.cloneDeep(CredentialList);
                credList.emptyListText = i18n._('No Credentials Matching This Type Have Been Created');
                $scope.list = credList;

                $scope.credential_default_params = {
                    order_by: 'name',
                    page_size: 5
                };

                $scope.credential_queryset = {
                    order_by: 'name',
                    page_size: 5
                };

                $scope.$watch('credentialKind', function(){
                    $scope.credential_queryset.page = 1;
                    $scope.credential_default_params.credential_type = $scope
                        .credential_queryset.credential_type = parseInt($scope
                            .credentialKind);

                    qs.search(GetBasePath('credentials'), $scope
                        .credential_default_params)
                            .then(res => {
                                $scope.credential_dataset = res.data;
                                $scope.credentials = $scope.credential_dataset
                                    .results;

                                if(!$scope.listRendered) {
                                    $scope.generateCredentialList();
                                    $scope.listRendered = true;
                                    $scope.showModal();
                                }
                            });
                });

                $scope.$watchCollection('selectedCredentials.extra', () => {
                    if($scope.credentials && $scope.credentials.length > 0) {
                        if($scope.selectedCredentials.extra &&
                            $scope.selectedCredentials.extra.length > 0 &&
                            parseInt($scope.credentialKind) !== $scope.credentialKinds.Machine) {
                            updateExtraCredentialsList();
                        } else if (parseInt($scope.credentialKind) !== $scope.credentialKinds.Machine) {
                            uncheckAllCredentials();
                        }
                    }
                });

                $scope.$watch('selectedCredentials.machine', () => {
                    if($scope.selectedCredentials &&
                        $scope.selectedCredentials.machine &&
                        parseInt($scope.credentialKind) === $scope.credentialKinds.Machine) {
                        updateMachineCredentialList();
                    } else {
                        uncheckAllCredentials();
                    }
                });

                $scope.$watch('selectedCredentials.vault', () => {
                    if($scope.selectedCredentials &&
                        $scope.selectedCredentials.vault &&
                        parseInt($scope.credentialKind) === $scope.credentialKinds.Vault) {
                        updateVaultCredentialList();
                    } else {
                        uncheckAllCredentials();
                    }
                });

                $scope.$watchGroup(['credentials',
                    'selectedCredentials.machine',
                    'selectedCredentials.vault'], () => {
                        if($scope.credentials &&
                            $scope.credentials.length > 0) {
                                if($scope.selectedCredentials &&
                                      $scope.selectedCredentials.machine &&
                                      parseInt($scope.credentialKind) === $scope.credentialKinds.Machine) {
                                          updateMachineCredentialList();
                                } else if($scope.selectedCredentials &&
                                      $scope.selectedCredentials.vault &&
                                      parseInt($scope.credentialKind) === $scope.credentialKinds.Vault) {
                                          updateVaultCredentialList();
                                } else if($scope.selectedCredentials &&
                                      $scope.selectedCredentials.extra &&
                                      $scope.selectedCredentials.extra.length > 0 &&
                                      parseInt($scope.credentialKind) !== $scope.credentialKinds.Machine) {
                                          updateExtraCredentialsList();
                                } else {
                                    uncheckAllCredentials();
                                }
                        }
                });
            };

            $scope.$on('multiCredentialModalLinked', function() {
                init();
            });

            $scope.toggle_row = function(selectedRow) {
                if(parseInt($scope.credentialKind) === $scope.credentialKinds.Machine) {
                    if($scope.selectedCredentials &&
                        $scope.selectedCredentials.machine &&
                        $scope.selectedCredentials.machine.id === selectedRow.id) {
                        $scope.selectedCredentials.machine = null;
                    } else {
                        $scope.selectedCredentials.machine = _.cloneDeep(selectedRow);
                    }
                }else if(parseInt($scope.credentialKind) === $scope.credentialKinds.Vault) {
                    if($scope.selectedCredentials &&
                        $scope.selectedCredentials.vault &&
                        $scope.selectedCredentials.vault.id === selectedRow.id) {
                        $scope.selectedCredentials.vault = null;
                    } else {
                        $scope.selectedCredentials.vault = _.cloneDeep(selectedRow);
                    }
                } else {
                    let rowDeselected = false;
                    for (let i = $scope.selectedCredentials.extra.length - 1; i >= 0; i--) {
                        if($scope.selectedCredentials.extra[i].id === selectedRow
                            .id) {
                                $scope.selectedCredentials.extra.splice(i, 1);
                                rowDeselected = true;
                        } else if(selectedRow.credential_type === $scope
                            .selectedCredentials.extra[i].credential_type) {
                                $scope.selectedCredentials.extra.splice(i, 1);
                        }
                    }
                    if(!rowDeselected) {
                        $scope.selectedCredentials.extra
                            .push(_.cloneDeep(selectedRow));
                    }
                }
            };

            $scope.selectedCredentialsDirty = function() {
                if ($scope.originalSelectedCredentials) {
                    return !($scope.originalSelectedCredentials.machine === null &&
                        $scope.originalSelectedCredentials.vault === null &&
                        $scope.originalSelectedCredentials.extra.length === 0) &&
                        !_.isEqual($scope.selectedCredentials,
                            $scope.originalSelectedCredentials);
                } else {
                    return false;
                }
            };

            $scope.revertToDefaultCredentials = function() {
                $scope.selectedCredentials = _.cloneDeep($scope.originalSelectedCredentials);
            };

            $scope.removeCredential = function(credToRemove) {
                [$scope.selectedCredentials,
                    $scope.credTags] = MultiCredentialService
                        .removeCredential(credToRemove,
                            $scope.selectedCredentials, $scope.credTags);

                if ($scope.credentials
                    .filter(cred => cred.id === credToRemove).length) {
                        uncheckAllCredentials();
                }
            };

            $scope.cancelForm = function() {
                $scope.selectedCredentials = $scope.originalSelectedCredentials;
                $scope.credTags = $scope.credentialsToPost;
                $scope.destroyModal();
            };

            $scope.saveForm = function() {
                $scope.credentialsToPost = $scope.credTags;
                $scope.destroyModal();
            };
        }]
    };
}];
