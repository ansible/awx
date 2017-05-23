/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Inventories
 * @description This controller's for the Inventory page
 */

function SmartInventoryAdd($scope, $location,
    GenerateForm, smartInventoryForm, rbacUiControlService, Rest, Alert, ProcessErrors,
    ClearScope, GetBasePath, ParseTypeChange, Wait, ToJSON,
    $state) {

    $scope.canAdd = false;
    rbacUiControlService.canAdd(GetBasePath('inventory'))
        .then(function(canAdd) {
            $scope.canAdd = canAdd;
        });

    Rest.setUrl(GetBasePath('inventory'));
    Rest.options()
        .success(function(data) {
            if (!data.actions.POST) {
                $state.go("^");
                Alert('Permission Error', 'You do not have permission to add an inventory.', 'alert-info');
            }
        });

    ClearScope();

    // Inject dynamic view
    var defaultUrl = GetBasePath('inventory'),
        form = smartInventoryForm;

    init();

    function init() {
        $scope.canEditOrg = true;
        form.formLabelSize = null;
        form.formFieldSize = null;

        // apply form definition's default field values
        GenerateForm.applyDefaults(form, $scope);

        $scope.parseType = 'yaml';
        ParseTypeChange({
            scope: $scope,
            variable: 'smartinventory_variables',
            parse_variable: 'parseType',
            field_id: 'smartinventory_smartinventory_variables'
        });

        $scope.smart_hosts = $state.params.hostfilter ? JSON.parse($state.params.hostfilter) : '';
    }

    // Save
    $scope.formSave = function() {
        Wait('start');
        try {
            let fld, data = {};

            for (fld in form.fields) {
                data[fld] = $scope[fld];
            }

            data.variables = ToJSON($scope.parseType, $scope.smartinventory_variables, true);

            let decodedHostFilter = decodeURIComponent($scope.smart_hosts.host_filter);
            decodedHostFilter = decodedHostFilter.replace(/__icontains_DEFAULT/g, "__icontains");
            decodedHostFilter = decodedHostFilter.replace(/__search_DEFAULT/g, "__search");
            data.host_filter = decodedHostFilter;

            data.kind = "smart";

            Rest.setUrl(defaultUrl);
            Rest.post(data)
                .success(function(data) {
                    var inventory_id = data.id;
                    Wait('stop');
                    $state.go('inventories.editSmartInventory', {smartinventory_id: inventory_id}, {reload: true});
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to add new inventory. Post returned status: ' + status
                    });
                });
        } catch (err) {
            Wait('stop');
            Alert("Error", "Error parsing inventory variables. Parser returned: " + err);
        }

    };

    $scope.formCancel = function() {
        $state.go('inventories');
    };
}

export default ['$scope', '$location',
    'GenerateForm', 'smartInventoryForm', 'rbacUiControlService', 'Rest', 'Alert',
    'ProcessErrors', 'ClearScope', 'GetBasePath', 'ParseTypeChange',
    'Wait', 'ToJSON', '$state', SmartInventoryAdd
];
