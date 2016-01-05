/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Permissions
 * @description This controller for permissions edit
*/
export default
    ['$scope', '$rootScope', '$compile', '$location', '$log', '$stateParams', 'permissionsForm', 'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'ReturnToCaller', 'ClearScope', 'Prompt', 'GetBasePath', 'InventoryList', 'ProjectList', 'LookUpInit', 'CheckAccess', 'Wait', 'permissionsCategoryChange', 'fieldChoices', 'fieldLabels',
        function($scope, $rootScope, $compile, $location, $log, $stateParams, permissionsForm, GenerateForm, Rest, Alert, ProcessErrors, ReturnToCaller, ClearScope, Prompt, GetBasePath, InventoryList, ProjectList, LookUpInit, CheckAccess, Wait, permissionsCategoryChange, fieldChoices, fieldLabels) {

            ClearScope();

            var generator = GenerateForm,
                form = permissionsForm,
                base_id = ($stateParams.user_id !== undefined) ? $stateParams.user_id : $stateParams.team_id,
                id = $stateParams.permission_id,
                defaultUrl = GetBasePath('base') + 'permissions/' + id + '/',
                base = $location.path().replace(/^\//, '').split('/')[0],
                master = {};

            $scope.permission_label = {};

            var permissionsChoice = fieldChoices({
                scope: $scope,
                url: 'api/v1/' + base + '/' + base_id + '/permissions/',
                field: 'permission_type'
            });

            permissionsChoice.then(function (choices) {
                return fieldLabels({
                    choices: choices
                });
            }).then(function (choices) {
                _.map(choices, function(n, key) {
                    $scope.permission_label[key] = n;
                });
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

            generator.inject(form, { mode: 'edit', related: true, scope: $scope });
            generator.reset();

            $scope.selectCategory = function (resetIn) {
                var reset = (resetIn === false) ? false : true;
                permissionsCategoryChange({ scope: $scope, reset: reset });
            };
            if ($scope.removeFillForm) {
                $scope.removeFillForm();
            }
            $scope.removeFillForm = $scope.$on('FillForm', function () {
                // Retrieve detail record and prepopulate the form
                Wait('start');
                Rest.setUrl(defaultUrl);
                Rest.get()
                    .success(function (data) {
                        var fld, sourceModel, sourceField;
                        for (fld in form.fields) {
                            if (data[fld]) {
                                if (form.fields[fld].sourceModel) {
                                    sourceModel = form.fields[fld].sourceModel;
                                    sourceField = form.fields[fld].sourceField;
                                    $scope[sourceModel + '_' + sourceField] = data.summary_fields[sourceModel][sourceField];
                                    master[sourceModel + '_' + sourceField] = data.summary_fields[sourceModel][sourceField];
                                }
                                $scope[fld] = data[fld];
                                master[fld] = $scope[fld];
                            }
                        }

                        $scope.category = 'Deploy';
                        if (data.permission_type !== 'run' && data.permission_type !== 'check' && data.permission_type !== 'create') {
                            $scope.category = 'Inventory';
                        }
                        master.category = $scope.category;
                        $scope.selectCategory(false); //call without resetting $scope.category value

                        LookUpInit({
                            scope: $scope,
                            form: form,
                            current_item: data.inventory,
                            list: InventoryList,
                            field: 'inventory',
                            input_type: "radio"
                        });

                        LookUpInit({
                            scope: $scope,
                            form: form,
                            current_item: data.project,
                            list: ProjectList,
                            field: 'project',
                            input_type: 'radio'
                        });

                        $scope.changeAdhocCommandCheckbox();

                        if (!$scope.PermissionAddAllowed) {
                            // If not a privileged user, disable access
                            $('form[name="permission_form"]').find('select, input, button').each(function () {
                                if ($(this).is('input') || $(this).is('select')) {
                                    $(this).attr('readonly', 'readonly');
                                }
                                if ($(this).is('input[type="checkbox"]') ||
                                    $(this).is('input[type="radio"]') ||
                                    $(this).is('button')) {
                                    $(this).attr('disabled', 'disabled');
                                }
                            });
                        }
                        Wait('stop');
                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                            msg: 'Failed to retrieve Permission: ' + id + '. GET status: ' + status });
                    });
            });

            CheckAccess({
                scope: $scope,
                callback: 'FillForm'
            });

            // Save changes to the parent
            $scope.formSave = function () {
                var fld, data = {};
                generator.clearApiErrors();
                Wait('start');
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

                Rest.setUrl(defaultUrl);
                if($scope.category === "Inventory"){
                    delete data.project;
                }
                Rest.put(data)
                    .success(function () {
                        Wait('stop');
                        ReturnToCaller(1);
                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, form, { hdr: 'Error!', msg: 'Failed to update Permission: ' +
                            $stateParams.id + '. PUT status: ' + status });
                    });
            };


            // Cancel
            $scope.formReset = function () {
                generator.reset();
                for (var fld in master) {
                    $scope[fld] = master[fld];
                }
                $scope.selectCategory(false);
            };

        }];
