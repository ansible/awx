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
    GetBasePath, ParseTypeChange, Wait, ToJSON,
    ParseVariableString, $state, OrgAdminLookup, $rootScope, resourceData,
    CreateSelect2, InstanceGroupsService, InstanceGroupsData, CanRemediate) {

    // Inject dynamic view
    let defaultUrl = GetBasePath('inventory'),
        form = InventoryForm,
        fld, data,
        inventoryData = resourceData.data,
        instance_group_url = inventoryData.related.instance_groups;

    init();

    function init() {
        form.formLabelSize = null;
        form.formFieldSize = null;

        $scope = angular.extend($scope, inventoryData);

        $scope.insights_credential_name = (inventoryData.summary_fields.insights_credential && inventoryData.summary_fields.insights_credential.name) ? inventoryData.summary_fields.insights_credential.name : null;
        $scope.insights_credential = (inventoryData.summary_fields.insights_credential && inventoryData.summary_fields.insights_credential.id) ? inventoryData.summary_fields.insights_credential.id : null;
        $scope.is_insights = (inventoryData.summary_fields.insights_credential && inventoryData.summary_fields.insights_credential.id) ? true : false;
        $scope.organization_name = inventoryData.summary_fields.organization.name;
        $scope.inventory_variables = inventoryData.variables === null || inventoryData.variables === '' ? '---' : ParseVariableString(inventoryData.variables);
        $scope.parseType = 'yaml';
        $scope.instance_groups = InstanceGroupsData;
        $scope.canRemediate = CanRemediate;

        OrgAdminLookup.checkForRoleLevelAdminAccess(inventoryData.organization, 'inventory_admin_role')
            .then(function(canEditOrg){
                $scope.canEditOrg = canEditOrg;
            });

        $scope.inventory_obj = inventoryData;
        $scope.inventory_name = inventoryData.name;
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
            .then(() => {
                InstanceGroupsService.editInstanceGroups(instance_group_url, $scope.instance_groups)
                    .then(() => {
                        Wait('stop');
                        $state.go($state.current, {}, { reload: true });
                    })
                    .catch(({data, status}) => {
                        ProcessErrors($scope, data, status, form, {
                            hdr: 'Error!',
                            msg: 'Failed to update instance groups. POST returned status: ' + status
                        });
                    });
            })
            .catch(({data, status}) => {
                ProcessErrors($scope, data, status, form, {
                    hdr: 'Error!',
                    msg: 'Failed to update inventory. PUT returned status: ' + status
                });
            });
    };

    $scope.formCancel = function() {
        $state.go('inventories');
    };

    $scope.remediateInventory = function(inv_id, insights_credential){
        $state.go('templates.addJobTemplate', {inventory_id: inv_id, credential_id: insights_credential});
    };

}

export default ['$scope', '$location',
    '$stateParams', 'InventoryForm', 'Rest',
    'ProcessErrors', 'GetBasePath', 'ParseTypeChange', 'Wait',
    'ToJSON', 'ParseVariableString',
    '$state', 'OrgAdminLookup', '$rootScope', 'resourceData', 'CreateSelect2',
    'InstanceGroupsService', 'InstanceGroupsData', 'CanRemediate',
    InventoriesEdit,
];
