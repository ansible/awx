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
    GetBasePath, ParseTypeChange, Wait, ToJSON,
    $state, canAdd, InstanceGroupsService) {

    $scope.canAdd = canAdd;

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

            data.host_filter = decodeURIComponent($scope.smart_hosts.host_filter);

            data.kind = "smart";

            Rest.setUrl(defaultUrl);
            Rest.post(data)
                .then(({data}) => {
                    const inventory_id = data.id,
                        instance_group_url = data.related.instance_groups;

                    InstanceGroupsService.addInstanceGroups(instance_group_url, $scope.instance_groups)
                        .then(() => {
                            Wait('stop');
                            $state.go('inventories.editSmartInventory', {smartinventory_id: inventory_id}, {reload: true});
                        })
                        .catch(({data, status}) => {
                            ProcessErrors($scope, data, status, form, {
                                hdr: 'Error!',
                                msg: 'Failed to post instance groups. POST returned ' +
                                    'status: ' + status
                            });
                        });
                })
                .catch(({data, status}) => {
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
    'ProcessErrors', 'GetBasePath', 'ParseTypeChange',
    'Wait', 'ToJSON', '$state', 'canAdd', 'InstanceGroupsService', SmartInventoryAdd
];
