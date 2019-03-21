/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import { N_ } from "../../i18n";

const user_type_options = [
 { type: 'normal', label: N_('Normal User') },
 { type: 'system_auditor', label: N_('System Auditor') },
 { type: 'system_administrator', label: N_('System Administrator') },
];

export default ['$scope', '$rootScope', 'UserForm', 'GenerateForm', 'Rest',
    'Alert', 'ProcessErrors', 'ReturnToCaller', 'GetBasePath',
    'Wait', 'CreateSelect2', '$state', '$location', 'i18n', 'canAdd',
    function($scope, $rootScope, UserForm, GenerateForm, Rest, Alert,
    ProcessErrors, ReturnToCaller, GetBasePath, Wait, CreateSelect2,
    $state, $location, i18n, canAdd) {

        var defaultUrl = GetBasePath('organizations'),
            form = UserForm;

        init();

        function init() {
            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);

            $scope.canAdd = canAdd;
            $scope.isAddForm = true;
            $scope.ldap_user = false;
            $scope.not_ldap_user = !$scope.ldap_user;
            $scope.ldap_dn = null;
            $scope.socialAuthUser = false;
            $scope.external_account = null;
            $scope.last_login = null;

            Rest.setUrl(GetBasePath('users'));
            Rest.options()
                .then(({data}) => {
                    if (!data.actions.POST) {
                        $state.go("^");
                        Alert(i18n._('Permission Error'), i18n._('You do not have permission to add a user.'), 'alert-info');
                    }
                });

            $scope.user_type_options = user_type_options;
            $scope.user_type = user_type_options[0];
            $scope.$watch('user_type', user_type_sync($scope));
            CreateSelect2({
                element: '#user_user_type',
                multiple: false
            });
        }

        function user_type_sync($scope) {
            return (type_option) => {
                $scope.is_superuser = false;
                $scope.is_system_auditor = false;
                switch (type_option.type) {
                    case 'system_administrator':
                        $scope.is_superuser = true;
                        break;
                    case 'system_auditor':
                        $scope.is_system_auditor = true;
                        break;
                }
            };
        }

        // Save
        $scope.formSave = function() {
            var fld, data = {};
            if ($scope[form.name + '_form'].$valid) {
                if ($scope.organization !== undefined && $scope.organization !== null && $scope.organization !== '') {
                    Rest.setUrl(defaultUrl + $scope.organization + '/users/');
                    for (fld in form.fields) {
                        if (form.fields[fld].realName) {
                            data[form.fields[fld].realName] = $scope[fld];
                        } else {
                            data[fld] = $scope[fld];
                        }
                    }
                    data.is_superuser = $scope.is_superuser;
                    data.is_system_auditor = $scope.is_system_auditor;
                    Wait('start');
                    Rest.post(data)
                        .then(({data}) => {
                            var base = $location.path().replace(/^\//, '').split('/')[0];
                            if (base === 'users') {
                                $rootScope.flashMessage = i18n._('New user successfully created!');
                                $rootScope.$broadcast("EditIndicatorChange", "users", data.id);
                                $state.go('users.edit', { user_id: data.id }, { reload: true });
                            } else {
                                ReturnToCaller(1);
                            }
                        })
                        .catch(({data, status}) => {
                            ProcessErrors($scope, data, status, form, { hdr: i18n._('Error!'), msg: i18n._('Failed to add new user. POST returned status: ') + status });
                        });
                } else {
                    $scope.organization_name_api_error = i18n._('A value is required');
                }
            }
        };

        $scope.formCancel = function() {
            $state.go('users');
        };

        // Password change
        $scope.clearPWConfirm = function() {
            // If password value changes, make sure password_confirm must be re-entered
            $scope.password_confirm = '';
            let passValidity = (!$scope.password || $scope.password === '') ? true : false;
            $scope[form.name + '_form'].password_confirm.$setValidity('awpassmatch', passValidity);
        };
    }
];
