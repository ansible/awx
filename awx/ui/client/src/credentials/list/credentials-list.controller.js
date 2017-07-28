/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'Rest', 'CredentialList', 'Prompt', 'ProcessErrors', 'GetBasePath',
        'Wait', '$state', '$filter', 'rbacUiControlService', 'Dataset', 'credentialType', 'i18n',
    function($scope, Rest, CredentialList, Prompt,
    ProcessErrors, GetBasePath, Wait, $state, $filter, rbacUiControlService, Dataset,
    credentialType, i18n) {

        var list = CredentialList,
            defaultUrl = GetBasePath('credentials');

        init();

        function init() {
            rbacUiControlService.canAdd('credentials')
                .then(function(params) {
                    $scope.canAdd = params.canAdd;
                });

            $scope.$watch(list.name, assignCredentialKinds);

            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            $scope.selected = [];
        }

        $scope.$on(`${list.iterator}_options`, function(event, data){
            $scope.options = data.data.actions.GET;
            optionsRequestDataProcessing();
        });

        $scope.$watchCollection(`${$scope.list.name}`, function() {
            optionsRequestDataProcessing();
        });

        function assignCredentialKinds () {
            if (!Array.isArray($scope[list.name])) {
                return;
            }

            $scope[list.name].forEach(credential => {
                credential.kind = credentialType.match('id', credential.credential_type).name;
            });
        }

        // iterate over the list and add fields like type label, after the
        // OPTIONS request returns, or the list is sorted/paginated/searched
        function optionsRequestDataProcessing(){
            if ($scope[list.name] !== undefined) {
                $scope[list.name].forEach(function(item, item_idx) {
                    var itm = $scope[list.name][item_idx];

                    // Set the item type label
                    if (list.fields.kind && $scope.options &&
                        $scope.options.hasOwnProperty('kind')) {
                            $scope.options.kind.choices.forEach(function(choice) {
                                if (choice[0] === item.kind) {
                                    itm.kind_label = choice[1];
                                }
                            });
                    }
                });
            }
        }

        $scope.addCredential = function() {
            $state.go('credentials.add');
        };

        $scope.editCredential = function(id) {
            $state.go('credentials.edit', { credential_id: id });
        };

        $scope.deleteCredential = function(id, name) {
            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                var url = defaultUrl + id + '/';
                Rest.setUrl(url);
                Rest.destroy()
                    .success(function() {

                        let reloadListStateParams = null;

                        if($scope.credentials.length === 1 && $state.params.credential_search && !_.isEmpty($state.params.credential_search.page) && $state.params.credential_search.page !== '1') {
                            reloadListStateParams = _.cloneDeep($state.params);
                            reloadListStateParams.credential_search.page = (parseInt(reloadListStateParams.credential_search.page)-1).toString();
                        }

                        if (parseInt($state.params.credential_id) === id) {
                            $state.go("^", reloadListStateParams, { reload: true });
                        } else {
                            $state.go('.', reloadListStateParams, {reload: true});
                        }
                        Wait('stop');
                    })
                    .error(function(data, status) {
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            Prompt({
                hdr: i18n._('Delete'),
                body: '<div class="Prompt-bodyQuery">' + i18n._('Are you sure you want to delete the credential below?') + '</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>',
                action: action,
                actionText: i18n._('DELETE')
            });
        };
    }
];
