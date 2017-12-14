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

                    const machineIsReadOnly = _.get(scope.selectedCredentials, 'machine.readOnly');
                    const vaultIsReadOnly = _.get(scope.selectedCredentials, 'vault.readOnly');

                    if (!machineIsReadOnly) {
                        scope.credentialKind = `${kinds.Machine}`;
                    } else if (!vaultIsReadOnly) {
                        scope.credentialKind = `${kinds.Vault}`;
                    } else {
                        scope.credentialKind = `${kinds.Network}`;
                    }

                    scope.showModal = function() {
                        scope.modalHidden = false;
                        $('#multi-credential-modal').modal('show');
                    };

                    scope.hideModal = function() {
                        scope.modalHidden = true;
                        scope.credentialKind = kinds.Machine;
                        $('#multi-credential-modal').modal('hide');
                    };

                    scope.generateCredentialList = function(inputType = 'radio') {
                        let html = GenerateList.build({
                            list: scope.list,
                            input_type: inputType,
                            mode: 'lookup'
                        });

                        $('#multi-credential-modal-body').append($compile(html)(scope));
                        scope.listRendered = true;
                    };

                    scope.destroyCredentialList = () => {
                        $('#multi-credential-modal-body').empty();
                        scope.listRendered = false;
                    }

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
                let extraCredIds = $scope.selectedCredentials.extra.map(cred => cred.id);
                $scope.credentials.forEach(cred => {
                    cred.checked = (extraCredIds.indexOf(cred.id) > - 1) ? 1 : 0;
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

            const onCredentialKindChanged = (newValue, oldValue) => {
                const newValueIsVault = (parseInt(newValue) === _.get($scope, 'credentialKinds.Vault'));
                const oldValueIsVault = (parseInt(oldValue) === _.get($scope, 'credentialKinds.Vault'));
                const isClosing = ((newValue !== oldValue) && $scope.modalHidden);

                if ((oldValueIsVault || newValueIsVault) && !isClosing) {
                    $scope.destroyCredentialList();
                }

                $scope.credential_queryset.page = 1;
                $scope.credential_default_params.credential_type = parseInt($scope.credentialKind);
                $scope.credential_queryset.credential_type = parseInt($scope.credentialKind);

                qs.search(GetBasePath('credentials'), $scope.credential_default_params)
                    .then(res => {
                        $scope.credential_dataset = res.data;
                        $scope.credentials = $scope.credential_dataset.results;

                        if(!$scope.listRendered) {
                            if (newValueIsVault) {
                                $scope.generateCredentialList('checkbox');
                            } else {
                                $scope.generateCredentialList();
                            }
                            updateExtraCredentialsList();
                            $scope.showModal();
                        }
                    });
            };

            let init = function() {
                $scope.originalSelectedCredentials = _.cloneDeep($scope.selectedCredentials);
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

                $scope.$watch('credentialKind', onCredentialKindChanged);

                $scope.$watchCollection('credentials', updateExtraCredentialsList);

                $scope.$watchCollection('selectedCredentials.extra', () => {
                    if($scope.credentials && $scope.credentials.length > 0) {
                        if($scope.selectedCredentials.extra &&
                            $scope.selectedCredentials.extra.length > 0) {
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

            $scope.toggle_credential = id => {
                // This is called only when a checkbox input is clicked directly. For clicks anywhere
                // else on the row or direct radio button clicks, the toggle_row handler is called
                // instead with a slightly different set of arguments. We normalize those arguments
                // here and pass them through to the other handler so that the behavior is consistent.
                const [credential] = $scope.credentials.filter(credential => credential.id === id);
                return $scope.toggle_row(credential);
            };

            $scope.toggle_row = function(selectedRow) {
                let rowDeselected = false;
                for (let i = $scope.selectedCredentials.extra.length - 1; i >= 0; i--) {
                    if($scope.selectedCredentials.extra[i].id === selectedRow.id) {
                        $scope.selectedCredentials.extra.splice(i, 1);
                        rowDeselected = true;
                    } else if(selectedRow.credential_type === $scope.selectedCredentials.extra[i].credential_type) {
                        if (selectedRow.credential_type !== $scope.credentialKinds.Vault) {
                            $scope.selectedCredentials.extra.splice(i, 1);
                        }
                    }
                }
                if(!rowDeselected) {
                    $scope.selectedCredentials.extra
                        .push(_.cloneDeep(selectedRow));
                }
            };

            $scope.selectedCredentialsDirty = function() {
                if ($scope.originalSelectedCredentials) {
                    return !($scope.originalSelectedCredentials.extra.length === 0) &&
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
                $scope.hideModal();
            };

            $scope.saveForm = function() {
                $scope.credentialsToPost = $scope.credTags;
                $scope.hideModal();
            };
        }]
    };
}];
