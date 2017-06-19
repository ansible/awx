export default ['templateUrl', 'Rest', 'GetBasePath', 'generateList', '$compile', 'CreateSelect2', 'i18n',
    function(templateUrl, Rest, GetBasePath, GenerateList, $compile, CreateSelect2, i18n) {
    return {
        restrict: 'E',
        scope: {
            credentialsToPost: '=',
            credentials: '=',
            selectedCredentials: '='
        },
        templateUrl: templateUrl('templates/job_templates/multi-credential/multi-credential-modal'),

        link: function(scope, element) {
            scope.credentialKind = "1";

            $('#multi-credential-modal').on('hidden.bs.modal', function () {
                $('#multi-credential-modal').off('hidden.bs.modal');
                $(element).remove();
            });

            CreateSelect2({
                element: `#multi-credential-kind-select`,
                multiple: false,
                placeholder: i18n._('Select a credential')
            });

            scope.showModal = function() {
                $('#multi-credential-modal').modal('show');
            };

            scope.destroyModal = function() {
                scope.credentialKind = 1;
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

            // Go out and get the credential types
            Rest.setUrl(GetBasePath('credential_types'));
            Rest.get()
                .success(function (credentialTypeData) {
                    let credential_types = {};
                    scope.credentialTypeOptions = [];
                    credentialTypeData.results.forEach((credentialType => {
                        credential_types[credentialType.id] = credentialType;
                        if(credentialType.kind
                            .match(/^(machine|cloud|net|ssh)$/)) {
                                scope.credentialTypeOptions.push({
                                    name: credentialType.name,
                                    value: credentialType.id
                                });
                        }
                    }));
                    scope.credential_types = credential_types;
                    scope.$emit('multiCredentialModalLinked');
                });
        },

        controller: ['$scope', 'CredentialList', 'i18n', 'QuerySet',
            'GetBasePath', function($scope, CredentialList, i18n, qs,
            GetBasePath) {

            let updateCredentialTags = function() {
                let machineCred = [];
                let extraCreds = [];

                if ($scope.selectedCredentials &&
                    $scope.selectedCredentials.machine) {
                        let mach = $scope.selectedCredentials.machine;
                        mach.postType = "machine";
                        machineCred = [$scope.selectedCredentials.machine];
                }

                if ($scope.selectedCredentials &&
                    $scope.selectedCredentials.extra) {
                    extraCreds = $scope.selectedCredentials.extra;
                }

                extraCreds = extraCreds.map(function(cred) {
                    cred.postType = "extra";

                    return cred;
                });

                let credTags = machineCred.concat(extraCreds);

                $scope.credTags = credTags.map(cred => ({
                  name: cred.name,
                  id: cred.id,
                  postType: cred.postType,
                  kind: $scope.credentialTypeOptions
                      .filter(type => {
                          return parseInt(cred.credential_type) === type.value;
                      })[0].name + ":"
                }));
            };

            let updateExtraCredentialsList = function() {
                let extraCredIds = $scope.selectedCredentials.extra
                    .map(cred => cred.id);
                $scope.credentials.forEach(cred => {
                    if (cred.credential_type !== 1) {
                        cred.checked = (extraCredIds
                            .indexOf(cred.id) > - 1) ? 1 : 0;
                    }
                });
                updateCredentialTags();
            };

            let updateMachineCredentialList = function() {
                $scope.credentials.forEach(cred => {
                    if (cred.credential_type === 1) {
                        cred.checked = ($scope.selectedCredentials
                            .machine !== null &&
                            cred.id === $scope.selectedCredentials
                                .machine.id) ? 1 : 0;
                    }
                });
                updateCredentialTags();
            };

            let uncheckAllCredentials = function() {
                $scope.credentials.forEach(cred => {
                    cred.checked = 0;
                });
                updateCredentialTags();
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
                            parseInt($scope.credentialKind) !== 1) {
                            updateExtraCredentialsList();
                        } else {
                            uncheckAllCredentials();
                        }
                    }
                });

                $scope.$watch('selectedCredentials.machine', () => {
                    if($scope.selectedCredentials &&
                        $scope.selectedCredentials.machine &&
                        parseInt($scope.credentialKind) === 1) {
                        updateMachineCredentialList();
                    } else {
                        uncheckAllCredentials();
                    }
                });

                $scope.$watchGroup(['credentials',
                    'selectedCredentials.machine'], () => {
                        if($scope.credentials &&
                            $scope.credentials.length > 0) {
                                if($scope.selectedCredentials &&
                                      $scope.selectedCredentials.machine &&
                                      parseInt($scope.credentialKind) === 1) {
                                          updateMachineCredentialList();
                                } else if($scope.selectedCredentials &&
                                      $scope.selectedCredentials.extra &&
                                      $scope.selectedCredentials.extra.length > 0 &&
                                      parseInt($scope.credentialKind) !== 1) {
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
                if(parseInt($scope.credentialKind) === 1) {
                    if($scope.selectedCredentials &&
                        $scope.selectedCredentials.machine &&
                        $scope.selectedCredentials.machine.id === selectedRow.id) {
                        $scope.selectedCredentials.machine = null;
                    } else {
                        $scope.selectedCredentials.machine = _.cloneDeep(selectedRow);
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

            $scope.removeCredential = function(credToRemove) {
                $scope.credTags
                    .forEach(function(cred) {
                        if (credToRemove === cred.id) {
                            if (cred.postType === 'machine') {
                                $scope.selectedCredentials[cred.postType] = null;
                            } else {
                                $scope.selectedCredentials[cred.postType] = $scope
                                    .selectedCredentials[cred.postType]
                                        .filter(cred => cred
                                            .id !== credToRemove);
                            }
                        }
                    });

                $scope.credTags = $scope.credTags
                    .filter(cred => cred.id !== credToRemove);

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
