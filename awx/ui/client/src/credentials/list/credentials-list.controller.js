/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'Rest', 'CredentialList', 'Prompt', 'ClearScope',
    'ProcessErrors', 'GetBasePath', 'Wait', '$state', '$filter',
    'rbacUiControlService', 'Dataset', 'i18n',
    function($scope, Rest, CredentialList, Prompt, ClearScope, ProcessErrors,
    GetBasePath, Wait, $state, $filter, rbacUiControlService, Dataset,
    i18n) {

        ClearScope();

        var list = CredentialList,
            defaultUrl = GetBasePath('credentials');

        init();

        function init() {
            rbacUiControlService.canAdd('credentials')
                .then(function(canAdd) {
                    $scope.canAdd = canAdd;
                });

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
                        if (parseInt($state.params.credential_id) === id) {
                            $state.go("^", null, { reload: true });
                        } else {
                            $state.go('.', null, {reload: true});
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
