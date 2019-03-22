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

function InventoriesAdd($scope, $location,
    GenerateForm, InventoryForm, rbacUiControlService, Rest, Alert, ProcessErrors,
    GetBasePath, ParseTypeChange, Wait, ToJSON,
    $state, canAdd, CreateSelect2, InstanceGroupsService) {

    $scope.canAdd = canAdd;

    // Inject dynamic view
    var defaultUrl = GetBasePath('inventory'),
        form = InventoryForm;

    init();

    function init() {
        $scope.canEditOrg = true;
        form.formLabelSize = null;
        form.formFieldSize = null;

        // apply form definition's default field values
        GenerateForm.applyDefaults(form, $scope);
    }

    // Save
    $scope.formSave = function() {
        Wait('start');
        try {
            var fld, data;

            data = {};
            for (fld in form.fields) {
                if (form.fields[fld].realName) {
                    data[form.fields[fld].realName] = $scope[fld];
                } else {
                    data[fld] = $scope[fld];
                }
            }

            Rest.setUrl(defaultUrl);
            Rest.post(data)
                .then(({data}) => {
                    const inventory_id = data.id,
                        instance_group_url = data.related.instance_groups;

                    InstanceGroupsService.addInstanceGroups(instance_group_url, $scope.instance_groups)
                        .then(() => {
                            Wait('stop');
                            $state.go('inventories.edit', {inventory_id: inventory_id}, {reload: true});
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
    'GenerateForm', 'InventoryForm', 'rbacUiControlService', 'Rest', 'Alert',
    'ProcessErrors', 'GetBasePath', 'ParseTypeChange',
    'Wait', 'ToJSON', '$state','canAdd', 'CreateSelect2', 'InstanceGroupsService', InventoriesAdd
];
