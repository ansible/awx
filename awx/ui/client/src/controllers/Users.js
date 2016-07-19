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

const user_type_options = [
    {type: 'normal'              , label: 'Normal User'          },
    {type: 'system_auditor'      , label: 'System Auditor'       },
    {type: 'system_administrator', label: 'System Administrator' },
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

export function UsersList($scope, $rootScope, $location, $log, $stateParams,
    Rest, Alert, UserList, GenerateList, Prompt, SearchInit, PaginateInit,
    ReturnToCaller, ClearScope, ProcessErrors, GetBasePath, SelectionInit,
    Wait, $state, Refresh, $filter) {

    ClearScope();

    var list = UserList,
        defaultUrl = GetBasePath('users'),
        generator = GenerateList,
        base = $location.path().replace(/^\//, '').split('/')[0],
        mode = (base === 'users') ? 'edit' : 'select',
        url = (base === 'organizations') ? GetBasePath('organizations') + $stateParams.organization_id + '/users/' :
            GetBasePath('teams') + $stateParams.team_id + '/users/';

    var injectForm = function() {
        generator.inject(UserList, { mode: mode, scope: $scope });
    };

    injectForm();

    $scope.$on("RefreshUsersList", function() {
        injectForm();
        Refresh({
            scope: $scope,
            set: 'users',
            iterator: 'user',
            url: GetBasePath('users') + "?order_by=username&page_size=" + $scope.user_page_size
        });
    });

    $scope.selected = [];

    if (mode === 'select') {
        SelectionInit({ scope: $scope, list: list, url: url, returnToCaller: 1 });
    }

    if ($scope.removePostRefresh) {
        $scope.removePostRefresh();
    }
    $scope.removePostRefresh = $scope.$on('PostRefresh', function () {
        // Cleanup after a delete
        Wait('stop');
        $('#prompt-modal').modal('hide');
    });

    $rootScope.flashMessage = null;
    SearchInit({
        scope: $scope,
        set: 'users',
        list: list,
        url: defaultUrl
    });
    PaginateInit({
        scope: $scope,
        list: list,
        url: defaultUrl
    });
    $scope.search(list.iterator);

    $scope.addUser = function () {
        $state.transitionTo('users.add');
    };

    $scope.editUser = function (id) {
        $state.transitionTo('users.edit', {user_id: id});
    };

    $scope.deleteUser = function (id, name) {

        var action = function () {
            //$('#prompt-modal').on('hidden.bs.modal', function () {
            //    Wait('start');
            //});
            $('#prompt-modal').modal('hide');
            Wait('start');
            var url = defaultUrl + id + '/';
            Rest.setUrl(url);
            Rest.destroy()
                .success(function () {
                    if (parseInt($state.params.user_id) === id) {
                        $state.go("^", null, {reload: true});
                    } else {
                        $scope.search(list.iterator);
                    }
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
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

UsersList.$inject = ['$scope', '$rootScope', '$location', '$log',
    '$stateParams', 'Rest', 'Alert', 'UserList', 'generateList', 'Prompt',
    'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
    'ProcessErrors', 'GetBasePath', 'SelectionInit', 'Wait', '$state',
    'Refresh', '$filter'
];





export function UsersAdd($scope, $rootScope, $compile, $location, $log,
    $stateParams, UserForm, GenerateForm, Rest, Alert, ProcessErrors,
    ReturnToCaller, ClearScope, GetBasePath, LookUpInit, OrganizationList,
    ResetForm, Wait, CreateSelect2, $state) {

    ClearScope();

    // Inject dynamic view
    var defaultUrl = GetBasePath('organizations'),
        form = UserForm,
        generator = GenerateForm;

    generator.inject(form, { mode: 'add', related: false, scope: $scope });
    ResetForm();

    $scope.ldap_user = false;
    $scope.not_ldap_user = !$scope.ldap_user;
    $scope.ldap_dn = null;
    $scope.socialAuthUser = false;

    generator.reset();

    $scope.user_type_options = user_type_options;
    $scope.user_type = user_type_options[0];
    $scope.$watch('user_type', user_type_sync($scope));

    CreateSelect2({
        element: '#user_user_type',
        multiple: false
    });

    // Configure the lookup dialog. If we're adding a user through the Organizations tab,
    // default the Organization value.
    LookUpInit({
        scope: $scope,
        form: form,
        current_item: ($stateParams.organization_id !== undefined) ? $stateParams.organization_id : null,
        list: OrganizationList,
        field: 'organization',
        input_type: 'radio'
    });

    if ($stateParams.organization_id) {
        $scope.organization = $stateParams.organization_id;
        Rest.setUrl(GetBasePath('organizations') + $stateParams.organization_id + '/');
        Rest.get()
            .success(function (data) {
                $scope.organization_name = data.name;
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                    msg: 'Failed to lookup Organization: ' + data.id + '. GET returned status: ' + status });
            });
    }

    // Save
    $scope.formSave = function () {
        var fld, data = {};
        generator.clearApiErrors();
        generator.checkAutoFill();
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
                    .success(function (data) {
                        var base = $location.path().replace(/^\//, '').split('/')[0];
                        if (base === 'users') {
                            $rootScope.flashMessage = 'New user successfully created!';
                            $rootScope.$broadcast("EditIndicatorChange", "users", data.id);
                            $state.go('users.edit', {user_id: data.id}, {reload: true});
                        }
                        else {
                            ReturnToCaller(1);
                        }
                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, form, { hdr: 'Error!', msg: 'Failed to add new user. POST returned status: ' + status });
                    });
            } else {
                $scope.organization_name_api_error = 'A value is required';
            }
        }
    };

    $scope.formCancel = function () {
        $state.transitionTo('users');
    };

    // Password change
    $scope.clearPWConfirm = function (fld) {
        // If password value changes, make sure password_confirm must be re-entered
        $scope[fld] = '';
        $scope[form.name + '_form'][fld].$setValidity('awpassmatch', false);
    };
}

UsersAdd.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log',
    '$stateParams', 'UserForm', 'GenerateForm', 'Rest', 'Alert',
    'ProcessErrors', 'ReturnToCaller', 'ClearScope', 'GetBasePath',
    'LookUpInit', 'OrganizationList', 'ResetForm', 'Wait', 'CreateSelect2', '$state'
];


export function UsersEdit($scope, $rootScope, $location,
    $stateParams, UserForm, GenerateForm, Rest, ProcessErrors,
    RelatedSearchInit, RelatedPaginateInit, ClearScope,
    GetBasePath, ResetForm, Wait, CreateSelect2 ,$state) {

    ClearScope();

    var defaultUrl = GetBasePath('users'),
        generator = GenerateForm,
        form = UserForm,
        master = {},
        id = $stateParams.user_id,
        relatedSets = {},
        set;

    generator.inject(form, { mode: 'edit', related: true, scope: $scope });
    generator.reset();

    $scope.user_type_options = user_type_options;
    $scope.user_type = user_type_options[0];
    $scope.$watch('user_type', user_type_sync($scope));

    var setScopeFields = function(data){
        _(data)
        .pick(function(value, key){
            return form.fields.hasOwnProperty(key) === true;
        })
        .forEach(function(value, key){
            $scope[key] = value;
        })
        .value();
        return;
    };

    $scope.convertApiUrl = function(str) {
        if (str) {
            return str.replace("api/v1", "#");
        } else {
            return null;
        }
    };

    var setScopeRelated = function(data, related){
        _(related)
            .pick(function(value, key){
                return data.related.hasOwnProperty(key) === true;
            })
            .forEach(function(value, key){
                relatedSets[key] = {
                    url: data.related[key],
                    iterator: value.iterator
                };
            })
        .value();
    };
    // prepares a data payload for a PUT request to the API
    var processNewData = function(fields){
        var data = {};
        _.forEach(fields, function(value, key){
            if ($scope[key] !== '' && $scope[key]  !== null && $scope[key] !== undefined){
             data[key] = $scope[key];
            }
        });
        data.is_superuser = $scope.is_superuser;
        data.is_system_auditor = $scope.is_system_auditor;
        return data;
    };

    var init = function(){
        var url = defaultUrl + id;
        Rest.setUrl(url);
        Wait('start');
        Rest.get(url).success(function(data){
            $scope.user_id = id;
            $scope.ldap_user = (data.ldap_dn !== null && data.ldap_dn !== undefined && data.ldap_dn !== '') ? true : false;
            $scope.not_ldap_user = !$scope.ldap_user;
            master.ldap_user = $scope.ldap_user;
            $scope.socialAuthUser = (data.auth.length > 0) ? true : false;

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


            setScopeFields(data);
            setScopeRelated(data, form.related);

            RelatedSearchInit({
                scope: $scope,
                form: form,
                relatedSets: relatedSets
            });
            RelatedPaginateInit({
                scope: $scope,
                relatedSets: relatedSets
            });

            for (set in relatedSets) {
                $scope.search(relatedSets[set].iterator);
            }

            Wait('stop');
        })
        .error(function (data, status) {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve user: ' +
            $stateParams.id + '. GET status: ' + status });
        });
    };

    $scope.formCancel = function(){
        $state.go('users', null, {reload: true});
    };

    $scope.formSave = function(){
        generator.clearApiErrors();
        generator.checkAutoFill();
        $rootScope.flashMessage = null;
        if ($scope[form.name + '_form'].$valid){
            Rest.setUrl(defaultUrl + id + '/');
            var data = processNewData(form.fields);
            Rest.put(data).success(function(){
                $state.go($state.current, null, {reload: true});
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve user: ' +
                $stateParams.id + '. GET status: ' + status });
            });
        }
    };

    $scope.clearPWConfirm = function (fld) {
        // If password value changes, make sure password_confirm must be re-entered
        $scope[fld] = '';
        $scope[form.name + '_form'][fld].$setValidity('awpassmatch', false);
        $rootScope.flashMessage = null;
    };

    init();

    /* Related Set implementation TDB */
}

UsersEdit.$inject = ['$scope', '$rootScope', '$location',
    '$stateParams', 'UserForm', 'GenerateForm', 'Rest', 'ProcessErrors',
    'RelatedSearchInit', 'RelatedPaginateInit', 'ClearScope', 'GetBasePath',
    'ResetForm', 'Wait', 'CreateSelect2', '$state'
];
