/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Users
 * @description This controller's the Users page
 */

import { N_ } from "../i18n";

const user_type_options = [
    { type: 'normal', label: N_('Normal User') },
    { type: 'system_auditor', label: N_('System Auditor') },
    { type: 'system_administrator', label: N_('System Administrator') },
];

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

export function UsersList($scope, $rootScope, $stateParams,
    Rest, Alert, UserList, Prompt, ClearScope, ProcessErrors, GetBasePath,
    Wait, $state, $filter, rbacUiControlService, Dataset, i18n) {

    for (var i = 0; i < user_type_options.length; i++) {
        user_type_options[i].label = i18n._(user_type_options[i].label);
    }

    ClearScope();

    var list = UserList,
        defaultUrl = GetBasePath('users');

    init();

    function init() {
        $scope.canAdd = false;

        rbacUiControlService.canAdd('users')
            .then(function(canAdd) {
                $scope.canAdd = canAdd;
            });

        // search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;


        $rootScope.flashMessage = null;
        $scope.selected = [];
    }

    $scope.addUser = function() {
        $state.go('users.add');
    };

    $scope.editUser = function(id) {
        $state.go('users.edit', { user_id: id });
    };

    $scope.deleteUser = function(id, name) {

        var action = function() {
            $('#prompt-modal').modal('hide');
            Wait('start');
            var url = defaultUrl + id + '/';
            Rest.setUrl(url);
            Rest.destroy()
                .success(function() {
                    if (parseInt($state.params.user_id) === id) {
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

        Prompt({
            hdr: 'Delete',
            body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the user below?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>',
            action: action,
            actionText: 'DELETE'
        });
    };
}

UsersList.$inject = ['$scope', '$rootScope', '$stateParams',
    'Rest', 'Alert', 'UserList', 'Prompt', 'ClearScope', 'ProcessErrors', 'GetBasePath',
    'Wait', '$state', '$filter', 'rbacUiControlService', 'Dataset', 'i18n'
];


export function UsersAdd($scope, $rootScope, $stateParams, UserForm,
    GenerateForm, Rest, Alert, ProcessErrors, ReturnToCaller, ClearScope,
    GetBasePath, ResetForm, Wait, CreateSelect2, $state, $location) {

    ClearScope();

    var defaultUrl = GetBasePath('organizations'),
        form = UserForm;

    init();

    function init() {
        // apply form definition's default field values
        GenerateForm.applyDefaults(form, $scope);

        $scope.ldap_user = false;
        $scope.not_ldap_user = !$scope.ldap_user;
        $scope.ldap_dn = null;
        $scope.socialAuthUser = false;
        $scope.external_account = null;

        Rest.setUrl(GetBasePath('users'));
        Rest.options()
            .success(function(data) {
                if (!data.actions.POST) {
                    $state.go("^");
                    Alert('Permission Error', 'You do not have permission to add a user.', 'alert-info');
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
                    .success(function(data) {
                        var base = $location.path().replace(/^\//, '').split('/')[0];
                        if (base === 'users') {
                            $rootScope.flashMessage = 'New user successfully created!';
                            $rootScope.$broadcast("EditIndicatorChange", "users", data.id);
                            $state.go('users.edit', { user_id: data.id }, { reload: true });
                        } else {
                            ReturnToCaller(1);
                        }
                    })
                    .error(function(data, status) {
                        ProcessErrors($scope, data, status, form, { hdr: 'Error!', msg: 'Failed to add new user. POST returned status: ' + status });
                    });
            } else {
                $scope.organization_name_api_error = 'A value is required';
            }
        }
    };

    $scope.formCancel = function() {
        $state.go('users');
    };

    // Password change
    $scope.clearPWConfirm = function(fld) {
        // If password value changes, make sure password_confirm must be re-entered
        $scope[fld] = '';
        $scope[form.name + '_form'][fld].$setValidity('awpassmatch', false);
    };
}

UsersAdd.$inject = ['$scope', '$rootScope', '$stateParams', 'UserForm', 'GenerateForm',
    'Rest', 'Alert', 'ProcessErrors', 'ReturnToCaller', 'ClearScope', 'GetBasePath',
    'ResetForm', 'Wait', 'CreateSelect2', '$state', '$location'
];

export function UsersEdit($scope, $rootScope, $location,
    $stateParams, UserForm, Rest, ProcessErrors,
    ClearScope, GetBasePath, ResetForm, Wait, CreateSelect2, $state, i18n) {

    for (var i = 0; i < user_type_options.length; i++) {
        user_type_options[i].label = i18n._(user_type_options[i].label);
    }
    ClearScope();

    var form = UserForm,
        master = {},
        id = $stateParams.user_id,
        defaultUrl = GetBasePath('users') + id;

    init();

    function init() {
        $scope.user_type_options = user_type_options;
        $scope.user_type = user_type_options[0];
        $scope.$watch('user_type', user_type_sync($scope));
        Rest.setUrl(defaultUrl);
        Wait('start');
        Rest.get(defaultUrl).success(function(data) {
                $scope.user_id = id;
                $scope.ldap_user = (data.ldap_dn !== null && data.ldap_dn !== undefined && data.ldap_dn !== '') ? true : false;
                $scope.not_ldap_user = !$scope.ldap_user;
                master.ldap_user = $scope.ldap_user;
                $scope.socialAuthUser = (data.auth.length > 0) ? true : false;
                $scope.external_account = data.external_account;

                $scope.user_type = $scope.user_type_options[0];
                $scope.is_system_auditor = false;
                $scope.is_superuser = false;
                if (data.is_system_auditor) {
                    $scope.user_type = $scope.user_type_options[1];
                    $scope.is_system_auditor = true;
                }
                if (data.is_superuser) {
                    $scope.user_type = $scope.user_type_options[2];
                    $scope.is_superuser = true;
                }

                $scope.user_obj = data;

                CreateSelect2({
                    element: '#user_user_type',
                    multiple: false
                });

                $scope.$watch('user_obj.summary_fields.user_capabilities.edit', function(val) {
                    if (val === false) {
                        $scope.canAdd = false;
                    }
                });

                setScopeFields(data);
                Wait('stop');
            })
            .error(function(data, status) {
                ProcessErrors($scope, data, status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to retrieve user: ' +
                        $stateParams.id + '. GET status: ' + status
                });
            });
    }


    function setScopeFields(data) {
        _(data)
            .pick(function(value, key) {
                return form.fields.hasOwnProperty(key) === true;
            })
            .forEach(function(value, key) {
                $scope[key] = value;
            })
            .value();
        return;
    }

    $scope.convertApiUrl = function(str) {
        if (str) {
            return str.replace("api/v1", "#");
        } else {
            return null;
        }
    };

    // prepares a data payload for a PUT request to the API
    var processNewData = function(fields) {
        var data = {};
        _.forEach(fields, function(value, key) {
            if ($scope[key] !== '' && $scope[key] !== null && $scope[key] !== undefined) {
                data[key] = $scope[key];
            }
        });
        data.is_superuser = $scope.is_superuser;
        data.is_system_auditor = $scope.is_system_auditor;
        return data;
    };

    $scope.formCancel = function() {
        $state.go('users', null, { reload: true });
    };

    $scope.formSave = function() {
        $rootScope.flashMessage = null;
        if ($scope[form.name + '_form'].$valid) {
            Rest.setUrl(defaultUrl + id + '/');
            var data = processNewData(form.fields);
            Rest.put(data).success(function() {
                    $state.go($state.current, null, { reload: true });
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to retrieve user: ' +
                            $stateParams.id + '. GET status: ' + status
                    });
                });
        }
    };

    $scope.clearPWConfirm = function(fld) {
        // If password value changes, make sure password_confirm must be re-entered
        $scope[fld] = '';
        $scope[form.name + '_form'][fld].$setValidity('awpassmatch', false);
        $rootScope.flashMessage = null;
    };
}

UsersEdit.$inject = ['$scope', '$rootScope', '$location',
    '$stateParams', 'UserForm', 'Rest', 'ProcessErrors', 'ClearScope', 'GetBasePath',
    'ResetForm', 'Wait', 'CreateSelect2', '$state', 'i18n'
];
