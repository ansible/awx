/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Permissions
 * @description This controller for permissions list
*/


export default
    ['$scope', '$rootScope', '$location', '$log', '$stateParams', 'Rest', 'Alert', 'permissionsList', 'generateList', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors', 'GetBasePath', 'CheckAccess', 'Wait', 'fieldChoices', 'fieldLabels', 'permissionsSearchSelect',
        function ($scope, $rootScope, $location, $log, $stateParams, Rest, Alert, permissionsList, GenerateList, Prompt, SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors, GetBasePath, CheckAccess, Wait, fieldChoices, fieldLabels, permissionsSearchSelect) {

            ClearScope();

            var list = permissionsList,
                base = $location.path().replace(/^\//, '').split('/')[0],
                base_id = ($stateParams.user_id !== undefined) ? $stateParams.user_id : $stateParams.team_id,
                defaultUrl = GetBasePath(base),
                generator = GenerateList;

            $scope.permission_label = {};
            $scope.permission_search_select = [];

            // return a promise from the options request with the permission type choices (including adhoc) as a param
            var permissionsChoice = fieldChoices({
                scope: $scope,
                url: 'api/v1/' + base + '/' + base_id + '/permissions/',
                field: 'permission_type'
            });

            // manipulate the choices from the options request to be set on
            // scope and be usable by the list form
            permissionsChoice.then(function (choices) {
                choices =
                    fieldLabels({
                        choices: choices
                    });
                _.map(choices, function(n, key) {
                    $scope.permission_label[key] = n;
                });
            });

            // manipulate the choices from the options request to be usable
            // by the search option for permission_type, you can't inject the
            // list until this is done!
            permissionsChoice.then(function (choices) {
                list.fields.permission_type.searchOptions =
                    permissionsSearchSelect({
                        choices: choices
                    });
                generator.inject(list, { mode: 'edit', scope: $scope });
            });

            defaultUrl += ($stateParams.user_id !== undefined) ? $stateParams.user_id : $stateParams.team_id;
            defaultUrl += '/permissions/';

            $scope.selected = [];

            CheckAccess({
                scope: $scope
            });

            if ($scope.removePostRefresh) {
                $scope.removePostRefresh();
            }
            $scope.removePostRefresh = $scope.$on('PostRefresh', function () {
                // Cleanup after a delete
                Wait('stop');
                $('#prompt-modal').modal('hide');
            });

            SearchInit({
                scope: $scope,
                set: 'permissions',
                list: list,
                url: defaultUrl
            });
            PaginateInit({
                scope: $scope,
                list: list,
                url: defaultUrl
            });
            $scope.search(list.iterator);

            $scope.addPermission = function () {
                if ($scope.PermissionAddAllowed) {
                    $location.path($location.path() + '/add');
                }
            };

            // if the permission includes adhoc (and is not admin), display that
            $scope.getPermissionText = function () {
                if (this.permission.permission_type !== "admin" && this.permission.run_ad_hoc_commands) {
                    return $scope.permission_label[this.permission.permission_type] +
                    " and " + $scope.permission_label.adhoc;
                } else {
                    return $scope.permission_label[this.permission.permission_type];
                }
            };

            $scope.editPermission = function (id) {
                $location.path($location.path() + '/' + id);
            };

            $scope.deletePermission = function (id, name) {
                var action = function () {
                    $('#prompt-modal').modal('hide');
                    Wait('start');
                    var url = GetBasePath('base') + 'permissions/' + id + '/';
                    Rest.setUrl(url);
                    Rest.destroy()
                        .success(function () {
                            $scope.search(list.iterator);
                        })
                        .error(function (data, status) {
                            Wait('stop');
                            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                        });
                };

                if ($scope.PermissionAddAllowed) {
                    Prompt({
                        hdr: 'Delete',
                        body: 'Are you sure you want to delete ' + name + '?',
                        action: action
                    });
                }
            };
        }];
