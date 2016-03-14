/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Inventories
 * @description This controller's for the Inventory page
 */

import '../job-templates/main';

function InventoriesAdd($scope, $rootScope, $compile, $location, $log,
    $stateParams, InventoryForm, GenerateForm, Rest, Alert, ProcessErrors,
    ReturnToCaller, ClearScope, generateList, OrganizationList, SearchInit,
    PaginateInit, LookUpInit, GetBasePath, ParseTypeChange, Wait, ToJSON,
    $state) {

    ClearScope();

    // Inject dynamic view
    var defaultUrl = GetBasePath('inventory'),
        form = InventoryForm(),
        generator = GenerateForm;

    form.well = true;
    form.formLabelSize = null;
    form.formFieldSize = null;

    generator.inject(form, { mode: 'add', related: false, scope: $scope });

    generator.reset();

    $scope.parseType = 'yaml';
    ParseTypeChange({
        scope: $scope,
        variable: 'variables',
        parse_variable: 'parseType',
        field_id: 'inventory_variables'
    });

    LookUpInit({
        scope:  $scope,
        form: form,
        current_item: ($stateParams.organization_id) ? $stateParams.organization_id : null,
        list: OrganizationList,
        field: 'organization',
        input_type: 'radio'
    });

    // Save
    $scope.formSave = function () {
        generator.clearApiErrors();
        Wait('start');
        try {
            var fld, json_data, data;

            json_data = ToJSON($scope.parseType, $scope.variables, true);

            data = {};
            for (fld in form.fields) {
                if (form.fields[fld].realName) {
                    data[form.fields[fld].realName] =  $scope[fld];
                } else {
                    data[fld] =  $scope[fld];
                }
            }

            Rest.setUrl(defaultUrl);
            Rest.post(data)
                .success(function (data) {
                    var inventory_id = data.id;
                    Wait('stop');
                    $location.path('/inventories/' + inventory_id + '/manage');
                })
                .error(function (data, status) {
                    ProcessErrors( $scope, data, status, form, { hdr: 'Error!',
                        msg: 'Failed to add new inventory. Post returned status: ' + status });
                });
        } catch (err) {
            Wait('stop');
            Alert("Error", "Error parsing inventory variables. Parser returned: " + err);
        }

    };

    $scope.formCancel = function () {
        $state.transitionTo('inventories');
    };
}

export default['$scope', '$rootScope', '$compile', '$location',
    '$log', '$stateParams', 'InventoryForm', 'GenerateForm', 'Rest', 'Alert',
    'ProcessErrors', 'ReturnToCaller', 'ClearScope', 'generateList',
    'OrganizationList', 'SearchInit', 'PaginateInit', 'LookUpInit',
    'GetBasePath', 'ParseTypeChange', 'Wait', 'ToJSON', '$state', InventoriesAdd]
