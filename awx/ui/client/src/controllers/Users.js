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


export function UsersList($scope, $rootScope, $location, $log, $stateParams,
    Rest, Alert, UserList, GenerateList, Prompt, SearchInit, PaginateInit,
    ReturnToCaller, ClearScope, ProcessErrors, GetBasePath, SelectionInit,
    Wait, $state, Refresh) {

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
                    $scope.search(list.iterator);
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the user below?</div><div class="Prompt-bodyTarget">' + name + '</div>',
            action: action,
            actionText: 'DELETE'
        });
    };
}

UsersList.$inject = ['$scope', '$rootScope', '$location', '$log',
    '$stateParams', 'Rest', 'Alert', 'UserList', 'generateList', 'Prompt',
    'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
    'ProcessErrors', 'GetBasePath', 'SelectionInit', 'Wait', '$state',
    'Refresh'
];


export function UsersAdd($scope, $rootScope, $compile, $location, $log,
    $stateParams, UserForm, GenerateForm, Rest, Alert, ProcessErrors,
    ReturnToCaller, ClearScope, GetBasePath, LookUpInit, OrganizationList,
    ResetForm, Wait, $state) {

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
                data.is_superuser = data.is_superuser || false;
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
    'LookUpInit', 'OrganizationList', 'ResetForm', 'Wait', '$state'
];


export function UsersEdit($scope, $rootScope, $location,
    $stateParams, UserForm, GenerateForm, Rest, ProcessErrors,
    RelatedSearchInit, RelatedPaginateInit, ClearScope,
    GetBasePath, ResetForm, Wait, $state) {

    ClearScope();

    var defaultUrl = GetBasePath('users'),
        generator = GenerateForm,
        form = UserForm,
        base = $location.path().replace(/^\//, '').split('/')[0],
        master = {},
        id = $stateParams.user_id,
        relatedSets = {};

    generator.inject(form, { mode: 'edit', related: true, scope: $scope });
    generator.reset();

    var setScopeFields = function(data){
        _(data)
        .pick(function(value, key){
            return form.fields.hasOwnProperty(key) === true;
        })
        .forEach(function(value, key){
            $scope[key] = value;
        })
        .value();
        return
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
        return data
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
            Rest.put(data).success(function(res){
                $state.go('users', null, {reload: true})
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
    'ResetForm', 'Wait', '$state'
];
