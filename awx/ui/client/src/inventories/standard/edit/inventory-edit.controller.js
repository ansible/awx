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

function InventoriesEdit($scope, $location,
    $stateParams, InventoryForm, Rest, ProcessErrors,
    ClearScope, GetBasePath, ParseTypeChange, Wait, ToJSON,
    ParseVariableString, $state, OrgAdminLookup, $rootScope, resourceData) {

    // Inject dynamic view
    var defaultUrl = GetBasePath('inventory'),
        form = InventoryForm,
        fld, data,
        inventoryData = resourceData.data;

    init();

    function init() {
        form.formLabelSize = null;
        form.formFieldSize = null;

        $scope = angular.extend($scope, inventoryData);

        $scope.credential_name = (inventoryData.summary_fields.insights_credential && inventoryData.summary_fields.insights_credential.name) ? inventoryData.summary_fields.insights_credential.name : null;
        $scope.organization_name = inventoryData.summary_fields.organization.name;
        $scope.inventory_variables = inventoryData.variables === null || inventoryData.variables === '' ? '---' : ParseVariableString(inventoryData.variables);
        $scope.parseType = 'yaml';

        $rootScope.$on('$stateChangeSuccess', function(event, toState) {
            if(toState.name === 'inventories.edit') {
                ParseTypeChange({
                    scope: $scope,
                    variable: 'inventory_variables',
                    parse_variable: 'parseType',
                    field_id: 'inventory_inventory_variables'
                });
            }
        });

        OrgAdminLookup.checkForAdminAccess({organization: inventoryData.organization})
        .then(function(canEditOrg){
            $scope.canEditOrg = canEditOrg;
        });

        $scope.inventory_obj = inventoryData;
        $rootScope.breadcrumb.inventory_name = inventoryData.name;

        $scope.$watch('inventory_obj.summary_fields.user_capabilities.edit', function(val) {
            if (val === false) {
                $scope.canAdd = false;
            }
        });
    }

    // Save
    $scope.formSave = function() {
        Wait('start');

        data = {};
        for (fld in form.fields) {
            if (form.fields[fld].realName) {
                data[form.fields[fld].realName] = $scope[fld];
            } else {
                data[fld] = $scope[fld];
            }
        }

        Rest.setUrl(defaultUrl + $stateParams.inventory_id + '/');
        Rest.put(data)
            .success(function() {
                Wait('stop');
                $state.go($state.current, {}, { reload: true });
            })
            .error(function(data, status) {
                ProcessErrors($scope, data, status, form, {
                    hdr: 'Error!',
                    msg: 'Failed to update inventory. PUT returned status: ' + status
                });
            });
    };

    $scope.formCancel = function() {
        $state.go('inventories');
    };

    $scope.remediateInventory = function(){
        $state.go('templates.addJobTemplate');
    };

}

export default ['$scope', '$location',
    '$stateParams', 'InventoryForm', 'Rest',
    'ProcessErrors', 'ClearScope', 'GetBasePath', 'ParseTypeChange', 'Wait',
    'ToJSON', 'ParseVariableString',
    '$state', 'OrgAdminLookup', '$rootScope', 'resourceData', InventoriesEdit,
];
