/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$rootScope', '$scope', 'Wait', 'CredentialTypesList',
    'GetBasePath', 'Rest', 'ProcessErrors', 'Prompt', '$state', '$filter',
    'Dataset', 'rbacUiControlService', 'Alert', '$q', 'CredentialTypeModel',
    'CredentialTypesStrings', 'i18n',
    function(
        $rootScope, $scope, Wait, CredentialTypesList,
        GetBasePath, Rest, ProcessErrors, Prompt, $state, $filter,
        Dataset, rbacUiControlService, Alert, $q, CredentialType,
        CredentialTypesStrings, i18n
    ) {
        let credentialType = new CredentialType();
        var defaultUrl = GetBasePath('credential_types'),
            list = CredentialTypesList;

        init();

        function init() {
            $scope.optionsDefer = $q.defer();

            if (!($rootScope.user_is_superuser || $rootScope.user_is_system_auditor)) {
                $state.go("setup");
                Alert('Permission Error', 'You do not have permission to view, edit or create custom credential types.', 'alert-info');
            }

            $scope.canAdd = false;

            rbacUiControlService.canAdd("credential_types")
                .then(function(params) {
                    $scope.canAdd = params.canAdd;
                    $scope.options = params.options;
                    $scope.optionsDefer.resolve(params.options);
                    optionsRequestDataProcessing();
                });

            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        }

        // @todo what is going on here, and if it needs to happen in this controller make $rootScope var name more explicit
        if ($rootScope.addedItem) {
            $scope.addedItem = $rootScope.addedItem;
            delete $rootScope.addedItem;
        }

        $scope.editCredentialType = function() {
            $state.go('credentialTypes.edit', {
                credential_type_id: this.credential_type.id
            });
        };

        $scope.deleteCredentialType = function(id, name) {

            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                var url = defaultUrl + id + '/';
                credentialType.request('delete', id)
                    .then(() => {

                        let reloadListStateParams = null;

                        if($scope.credential_types.length === 1 && $state.params.credential_type_search && _.has($state, 'params.credential_type_search.page') && $state.params.credential_type_search.page !== '1') {
                            reloadListStateParams = _.cloneDeep($state.params);
                            reloadListStateParams.credential_type_search.page = (parseInt(reloadListStateParams.credential_type_search.page)-1).toString();
                        }

                        if (parseInt($state.params.credential_type_id) === id) {
                            $state.go('^', reloadListStateParams, { reload: true });
                        } else {
                            $state.go('.', reloadListStateParams, { reload: true });
                        }
                    })
                    .catch(({data, status}) => {
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            credentialType.getDependentResourceCounts(id)
                .then((counts) => {
                    let credentialTypeInUse = false;
                    let deleteModalBody = `<div class="Prompt-bodyQuery">${CredentialTypesStrings.get('deleteResource.CONFIRM', 'credential type')}</div>`;

                    counts.forEach(countObj => {
                        if(countObj.count && countObj.count > 0) {
                            credentialTypeInUse = true;
                        }
                    });

                    if (credentialTypeInUse) {
                        deleteModalBody = `<div class="Prompt-bodyQuery">${CredentialTypesStrings.get('deleteCredentialType.CREDENTIAL_TYPE_IN_USE')}</div>`;
                    }

                    Prompt({
                        hdr: i18n._('Delete') + ' ' + $filter('sanitize')(name),
                        body: deleteModalBody,
                        action: action,
                        hideActionButton: credentialTypeInUse ? true : false,
                        actionText: i18n._('DELETE')
                    });
                });
        };

        $scope.addCredentialType = function() {
            $state.go('credentialTypes.add');
        };

        // iterate over the list and add fields like type label, after the
        // OPTIONS request returns, or the list is sorted/paginated/searched
        function optionsRequestDataProcessing(){
            $scope.optionsDefer.promise.then(function(options) {
                if($scope.list.name === 'credential_types'){
                    if ($scope[list.name] !== undefined) {
                        $scope[list.name].forEach(function(item, item_idx) {
                            var itm = $scope[list.name][item_idx];
                            // Set the item type label
                            if (list.fields.kind && options && options.actions && options.actions.GET && options.actions.GET.kind) {
                                options.actions.GET.kind.choices.forEach(function(choice) {
                                    if (choice[0] === item.kind) {
                                        itm.kind_label = choice[1];
                                    }
                                });
                            }

                        });
                    }
                }
            });
        }

        $scope.$watchCollection(`${$scope.list.name}`, function() {
                optionsRequestDataProcessing();
            }
        );

    }
];
