/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state', '$stateParams', '$scope', 'HostForm', 'ParseTypeChange',
    'GenerateForm', 'HostManageService', 'rbacUiControlService', 'GetBasePath',
    function($state, $stateParams, $scope, HostForm, ParseTypeChange,
        GenerateForm, HostManageService, rbacUiControlService, GetBasePath) {

        init();

        function init() {
            $scope.canAdd = false;

            rbacUiControlService.canAdd(GetBasePath('inventory') + $stateParams.inventory_id + "/hosts")
                .then(function(canAdd) {
                    $scope.canAdd = canAdd;
                });
            $scope.parseType = 'yaml';
            $scope.host = { enabled: true };
            // apply form definition's default field values
            GenerateForm.applyDefaults(HostForm, $scope);

            ParseTypeChange({
                scope: $scope,
                field_id: 'host_variables',
                variable: 'variables',
                parse_variable: 'parseType'
            });
        }
        $scope.formCancel = function() {
            $state.go('^');
        };
        $scope.toggleHostEnabled = function() {
            $scope.host.enabled = !$scope.host.enabled;
        };
        $scope.formSave = function() {
            var params = {
                variables: $scope.variables === '---' || $scope.variables === '{}' ? null : $scope.variables,
                name: $scope.name,
                description: $scope.description,
                enabled: $scope.host.enabled,
                inventory: $stateParams.inventory_id
            };
            HostManageService.post(params).then(function(res) {
                // assign the host to current group if not at the root level
                if ($stateParams.group) {
                    HostManageService.associateGroup(res.data, _.last($stateParams.group)).then(function() {
                        $state.go('inventoryManage.editHost', { host_id: res.data.id }, { reload: true });
                    });
                } else {
                    $state.go('inventoryManage.editHost', { host_id: res.data.id }, { reload: true });
                }
            });
        };
    }
];
