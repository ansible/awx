/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   '$scope', 'CredentialList', 'i18n', 'QuerySet', 'GetBasePath', 'credentialTypesLookup',
        function($scope, CredentialList, i18n, qs, GetBasePath, credentialTypesLookup) {
            let credentialKinds = {};

            let updateExtraCredentialsList = function() {
                $scope.credentials.forEach((row, i) => {
                    $scope.credentials[i].checked = 0;
                    $scope.selectedCredentials.extra.forEach((extraCredential, j) => {
                        if (row.id === $scope.selectedCredentials.extra[j].id) {
                            $scope.credentials[i].checked = 1;
                        }
                    });
                });
            };

            let updateMachineCredentialList = function() {
                $scope.credentials.forEach((row, i) => {
                    $scope.credentials[i].checked = 0;
                    if (row.id === $scope.selectedCredentials.machine.id) {
                        $scope.credentials[i].checked = 1;
                    }
                });
            };

            let uncheckAllCredentials = function() {
                $scope.credentials.forEach((row, i) => {
                    $scope.credentials[i].checked = 0;
                });
            };

            let init = function() {
                $scope.credential_dataset = [];
                $scope.credentials = [];
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
                    $scope.credential_default_params.credential_type = $scope.credential_queryset.credential_type = parseInt($scope.credentialKind);

                    qs.search(GetBasePath('credentials'), $scope.credential_default_params)
                        .then(res => {
                            $scope.credential_dataset = res.data;
                            $scope.credentials = $scope.credential_dataset.results;
                            if(!$scope.listRendered) {
                                $scope.generateCredentialList();
                                $scope.listRendered = true;
                            }
                        });
                });

                $scope.$watchCollection('selectedCredentials.extra', () => {
                    if($scope.credentials && $scope.credentials.length > 0) {
                        if($scope.selectedCredentials.extra && $scope.selectedCredentials.extra.length > 0 && parseInt($scope.credentialKind) !== credentialKinds.ssh) {
                            updateExtraCredentialsList();
                        } else if (parseInt($scope.credentialKind) !== credentialKinds.ssh) {
                            uncheckAllCredentials();
                        }
                    }
                });

                $scope.$watch('selectedCredentials.machine', () => {
                    if($scope.credentials && $scope.credentials.length > 0) {
                        if($scope.selectedCredentials.machine && parseInt($scope.credentialKind) === credentialKinds.ssh) {
                            updateMachineCredentialList();
                        }
                        else {
                            uncheckAllCredentials();
                        }
                    }
                });

                $scope.$watchGroup(['credentials', 'selectedCredentials.machine'], () => {
                    if($scope.credentials && $scope.credentials.length > 0) {
                        if($scope.selectedCredentials.machine && parseInt($scope.credentialKind) === credentialKinds.ssh) {
                            updateMachineCredentialList();
                        }
                        else if($scope.selectedCredentials.extra && $scope.selectedCredentials.extra.length > 0 && parseInt($scope.credentialKind) !== credentialKinds.ssh) {
                            updateExtraCredentialsList();
                        }
                        else {
                            uncheckAllCredentials();
                        }
                    }
                });
            };

            $scope.toggle_row = function(selectedRow) {
                if(parseInt($scope.credentialKind) === credentialKinds.ssh) {
                    $scope.selectedCredentials.machine = _.cloneDeep(selectedRow);
                }
                else {
                    for (let i = $scope.selectedCredentials.extra.length - 1; i >= 0; i--) {
                        if(selectedRow.credential_type === $scope.selectedCredentials.extra[i].credential_type) {
                            $scope.selectedCredentials.extra.splice(i, 1);
                        }
                    }
                    $scope.selectedCredentials.extra.push(_.cloneDeep(selectedRow));
                }
            };

            credentialTypesLookup()
                .then(kinds => {
                    credentialKinds = kinds;
                    init();
                });
        }
    ];
