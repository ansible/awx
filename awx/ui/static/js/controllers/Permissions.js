/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Permissions.js
 *
 *  Controller functions for Permissions model.
 *
 */
/**
 * @ngdoc function
 * @name controllers.function:Permissions
 * @description This controller's for permissions
*/


export function PermissionsList($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, PermissionList,
    GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors,
    GetBasePath, CheckAccess, Wait) {

    ClearScope();

    var list = PermissionList,
        base = $location.path().replace(/^\//, '').split('/')[0],
        defaultUrl = GetBasePath(base),
        generator = GenerateList;

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
}

PermissionsList.$inject = ['$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'PermissionList',
    'GenerateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller',
    'ClearScope', 'ProcessErrors', 'GetBasePath', 'CheckAccess', 'Wait'
];


export function PermissionsAdd($scope, $rootScope, $compile, $location, $log, $routeParams, PermissionsForm,
    GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope,
    GetBasePath, ReturnToCaller, InventoryList, ProjectList, LookUpInit, CheckAccess,
    Wait, PermissionCategoryChange) {

    ClearScope();

    // Inject dynamic view
    var form = PermissionsForm,
        generator = GenerateForm,
        id = ($routeParams.user_id !== undefined) ? $routeParams.user_id : $routeParams.team_id,
        base = $location.path().replace(/^\//, '').split('/')[0],
        master = {};

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
            url = (base === 'teams') ? GetBasePath('teams') + id + '/permissions/' : GetBasePath('users') + id + '/permissions/';
            Rest.setUrl(url);
            Rest.post(data)
                .success(function () {
                    Wait('stop');
                    ReturnToCaller(1);
                })
                .error(function (data, status) {
                    Wait('stop');
                    ProcessErrors($scope, data, status, PermissionsForm, { hdr: 'Error!',
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
        PermissionCategoryChange({ scope: $scope, reset: true });
    };


    $scope.selectCategory();

}

PermissionsAdd.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'PermissionsForm',
    'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath', 'ReturnToCaller',
    'InventoryList', 'ProjectList', 'LookUpInit', 'CheckAccess', 'Wait', 'PermissionCategoryChange'
];


export function PermissionsEdit($scope, $rootScope, $compile, $location, $log, $routeParams, PermissionsForm,
    GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope, Prompt, GetBasePath,
    InventoryList, ProjectList, LookUpInit, CheckAccess, Wait, PermissionCategoryChange) {

    ClearScope();

    var generator = GenerateForm,
        form = PermissionsForm,
        base_id = ($routeParams.user_id !== undefined) ? $routeParams.user_id : $routeParams.team_id,
        id = $routeParams.permission_id,
        defaultUrl = GetBasePath('base') + 'permissions/' + id + '/',
        master = {};

    generator.inject(form, { mode: 'edit', related: true, scope: $scope });
    generator.reset();




    $scope.selectCategory = function (resetIn) {
        var reset = (resetIn === false) ? false : true;
        PermissionCategoryChange({ scope: $scope, reset: reset });
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
                LoadBreadCrumbs({ path: '/users/' + base_id + '/permissions/' + id, title: data.name });
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
                    $routeParams.id + '. PUT status: ' + status });
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

}

PermissionsEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'PermissionsForm',
    'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'Prompt', 'GetBasePath',
    'InventoryList', 'ProjectList', 'LookUpInit', 'CheckAccess', 'Wait', 'PermissionCategoryChange'
];