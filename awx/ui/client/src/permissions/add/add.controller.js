/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Permissions
 * @description This controller for permissions add
*/
export default
    ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'permissionsForm', 'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath', 'ReturnToCaller', 'InventoryList', 'ProjectList', 'LookUpInit', 'CheckAccess', 'Wait', 'permissionsCategoryChange', 'permissionsChoices', 'permissionsLabel',
        function($scope, $rootScope, $compile, $location, $log, $routeParams, permissionsForm, GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, GetBasePath, ReturnToCaller, InventoryList, ProjectList, LookUpInit, CheckAccess, Wait, permissionsCategoryChange, permissionsChoices, permissionsLabel) {

            ClearScope();

            // Inject dynamic view
            var form = permissionsForm,
                generator = GenerateForm,
                id = ($routeParams.user_id !== undefined) ? $routeParams.user_id : $routeParams.team_id,
                base = $location.path().replace(/^\//, '').split('/')[0],
                master = {};

            var permissionsChoice = permissionsChoices({
                scope: $scope,
                url: 'api/v1/' + base + '/' + id + '/permissions/'
            });

            permissionsChoice.then(function (choices) {
                return permissionsLabel({
                    choices: choices
                });
            }).then(function (choices) {
                _.map(choices, function(n, key) {
                    $scope.permission_label[key] = n;
                });
            });

            generator.inject(form, { mode: 'add', related: false, scope: $scope });
            CheckAccess({ scope: $scope });
            generator.reset();
            LoadBreadCrumbs();

            $scope.inventoryrequired = true;
            $scope.projectrequired = false;
            $scope.category = 'Inventory';
            master.category = 'Inventory';
            master.inventoryrequired = true;
            master.projectrequired = false;
            $scope.run_ad_hoc_commands = false;
            $scope.permission_label = {};

            LookUpInit({
                scope: $scope,
                form: form,
                current_item: null,
                list: InventoryList,
                field: 'inventory',
                input_type: 'radio'
            });

            LookUpInit({
                scope: $scope,
                form: form,
                current_item: null,
                list: ProjectList,
                field: 'project',
                input_type: 'radio'
            });

            $scope.$watch("category", function(val) {
                if (val === 'Deploy') {
                    $scope.projectrequired = true;
                    LookUpInit({
                        scope: $scope,
                        form: form,
                        current_item: null,
                        list: ProjectList,
                        field: 'project',
                        input_type: 'radio'
                    });
                } else {
                    $scope.projectrequired = false;
                }
            });

            $scope.changeAdhocCommandCheckbox = function () {
                if ($scope.category === 'Deploy') {
                    $scope.run_ad_hoc_command = false;
                } else {
                    if ($scope.permission_type === 'admin') {
                        $scope.run_ad_hoc_commands = true;
                        $("#permission_run_ad_hoc_commands_chbox").attr("disabled", true);
                    } else  {
                        if (!$scope.run_ad_hoc_commands) {
                            $scope.run_ad_hoc_commands = false;
                        }
                        $("#permission_run_ad_hoc_commands_chbox").attr("disabled", false);
                    }
                }
            };

            // Save
            $scope.formSave = function () {
                var fld, url, data = {};
                generator.clearApiErrors();
                Wait('start');
                if ($scope.PermissionAddAllowed) {
                    data = {};
                    for (fld in form.fields) {
                        data[fld] = $scope[fld];
                    }
                    // job template (or deploy) based permissions do not have the run
                    // ad hoc commands parameter
                    if (data.category === "Deploy") {
                        data.run_ad_hoc_commands = false;
                    } else {
                        delete data.project;
                    }

                    url = (base === 'teams') ? GetBasePath('teams') + id + '/permissions/' : GetBasePath('users') + id + '/permissions/';
                    Rest.setUrl(url);
                    Rest.post(data)
                        .success(function () {
                            Wait('stop');
                            ReturnToCaller(1);
                        })
                        .error(function (data, status) {
                            Wait('stop');
                            ProcessErrors($scope, data, status, permissionsForm, { hdr: 'Error!',
                                msg: 'Failed to create new permission. Post returned status: ' + status });
                        });
                } else {
                    Alert('Access Denied', 'You do not have access to create new permission objects. Please contact a system administrator.',
                        'alert-danger');
                }
            };

            // Cancel
            $scope.formReset = function () {
                $rootScope.flashMessage = null;
                generator.reset();
                for (var fld in master) {
                    $scope[fld] = master[fld];
                }
                $scope.selectCategory();
            };

            $scope.selectCategory = function () {
                permissionsCategoryChange({ scope: $scope, reset: true });
            };


            $scope.selectCategory();

        }];
