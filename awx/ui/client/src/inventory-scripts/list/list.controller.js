/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$rootScope', '$scope', 'Wait', 'generateList', 'InventoryScriptsList',
    'GetBasePath', 'Rest', 'ProcessErrors', 'Prompt', '$state', '$filter', 'Dataset', 'rbacUiControlService',
    function(
        $rootScope, $scope, Wait, GenerateList, InventoryScriptsList,
        GetBasePath, Rest, ProcessErrors, Prompt, $state, $filter, Dataset, rbacUiControlService
    ) {
        var defaultUrl = GetBasePath('inventory_scripts'),
            list = InventoryScriptsList;

        init();

        function init() {
            $scope.canAdd = false;

            rbacUiControlService.canAdd("inventory_scripts")
                .then(function(canAdd) {
                    $scope.canAdd = canAdd;
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

        $scope.editCustomInv = function() {
            $state.go('inventoryScripts.edit', {
                inventory_script_id: this.inventory_script.id
            });
        };

        $scope.deleteCustomInv = function(id, name) {

            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                var url = defaultUrl + id + '/';
                Rest.setUrl(url);
                Rest.destroy()
                    .success(function() {
                        if (parseInt($state.params.inventory_script_id) === id) {
                            $state.go('^', null, { reload: true });
                        } else {
                            $state.go('.', null, { reload: true });
                        }
                    })
                    .error(function(data, status) {
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            var bodyHtml = '<div class="Prompt-bodyQuery">Are you sure you want to delete the inventory script below?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>';
            Prompt({
                hdr: 'Delete',
                body: bodyHtml,
                action: action,
                actionText: 'DELETE'
            });
        };

        $scope.addCustomInv = function() {
            $state.go('inventoryScripts.add');
        };

    }
];
