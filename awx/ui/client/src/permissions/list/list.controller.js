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
    ['$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'permissionsList', 'generateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors', 'GetBasePath', 'CheckAccess', 'Wait', 'permissionsLabel',
        function ($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, permissionsList, GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors, GetBasePath, CheckAccess, Wait, permissionsLabel) {

            ClearScope();

            var list = permissionsList,
                base = $location.path().replace(/^\//, '').split('/')[0],
                base_id = ($routeParams.user_id !== undefined) ? $routeParams.user_id : $routeParams.team_id,
                defaultUrl = GetBasePath(base),
                generator = GenerateList;

            $scope.permission_label = {};

            permissionsLabel({
                scope: $scope,
                url: 'api/v1/' + base + '/' + base_id + '/permissions/'
            }).then(function(choices) {
                _.map(choices, function(n, key) {
                    $scope.permission_label[key] = n;
                });
            });

            generator.inject(list, { mode: 'edit', scope: $scope, breadCrumbs: true });
            defaultUrl += ($routeParams.user_id !== undefined) ? $routeParams.user_id : $routeParams.team_id;
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

            LoadBreadCrumbs();

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
