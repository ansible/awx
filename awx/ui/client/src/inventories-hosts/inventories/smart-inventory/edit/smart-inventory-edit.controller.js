/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

function SmartInventoryEdit($scope, $location,
    $stateParams, InventoryForm, Rest, ProcessErrors,
    GetBasePath, ParseTypeChange, Wait, ToJSON,
    ParseVariableString, $state, OrgAdminLookup, resourceData,
    $rootScope, InstanceGroupsService, InstanceGroupsData) {

    // Inject dynamic view
    var defaultUrl = GetBasePath('inventory'),
        form = InventoryForm,
        inventory_id = $stateParams.smartinventory_id,
        inventoryData = resourceData.data,
        instance_group_url = inventoryData.related.instance_groups;
    init();

    function init() {
        form.formLabelSize = null;
        form.formFieldSize = null;
        $scope.inventory_id = inventory_id;

        $scope = angular.extend($scope, inventoryData);

        $scope.smartinventory_variables = inventoryData.variables === null || inventoryData.variables === '' ? '---' : ParseVariableString(inventoryData.variables);
        $scope.organization_name = inventoryData.summary_fields.organization.name;
        $scope.instance_groups = InstanceGroupsData;

        $scope.$watch('inventory_obj.summary_fields.user_capabilities.edit', function(val) {
            if (val === false) {
                $scope.canAdd = false;
            }
        });

        $scope.parseType = 'yaml';

        $scope.inventory_obj = inventoryData;
        $rootScope.breadcrumb.inventory_name = inventoryData.name;

        ParseTypeChange({
            scope: $scope,
            variable: 'smartinventory_variables',
            parse_variable: 'parseType',
            field_id: 'smartinventory_smartinventory_variables',
            readOnly: !$scope.inventory_obj.summary_fields.user_capabilities.edit
        });

        OrgAdminLookup.checkForAdminAccess({organization: inventoryData.organization})
        .then(function(canEditOrg){
            $scope.canEditOrg = canEditOrg;
        });

        $scope.smart_hosts = {
            host_filter: encodeURIComponent($scope.host_filter)
        };
    }

    // Save
    $scope.formSave = function() {
        Wait('start');

        let fld, data = {};

        for (fld in form.fields) {
            data[fld] = $scope[fld];
        }

        data.variables = ToJSON($scope.parseType, $scope.smartinventory_variables, true);
        data.host_filter = decodeURIComponent($scope.smart_hosts.host_filter);
        data.kind = "smart";

        Rest.setUrl(defaultUrl + inventory_id + '/');
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

}

export default [ '$scope', '$location',
    '$stateParams', 'InventoryForm', 'Rest',
    'ProcessErrors', 'GetBasePath', 'ParseTypeChange', 'Wait',
    'ToJSON', 'ParseVariableString',
    '$state', 'OrgAdminLookup', 'resourceData',
    '$rootScope', 'InstanceGroupsService', 'InstanceGroupsData', SmartInventoryEdit
];
