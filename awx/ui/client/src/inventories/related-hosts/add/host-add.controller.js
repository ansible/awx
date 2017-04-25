/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state', '$stateParams', '$scope', 'RelatedHostsFormDefinition', 'ParseTypeChange',
                'GenerateForm', 'HostManageService', 'rbacUiControlService', 'GetBasePath', 'ToJSON',
                function($state, $stateParams, $scope, RelatedHostsFormDefinition, ParseTypeChange,
                         GenerateForm, HostManageService, rbacUiControlService, GetBasePath, ToJSON) {

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
            GenerateForm.applyDefaults(RelatedHostsFormDefinition, $scope);

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
            if ($scope.host.has_inventory_sources){
                return;
            }
            $scope.host.enabled = !$scope.host.enabled;
        };
        $scope.formSave = function(){
            var json_data = ToJSON($scope.parseType, $scope.variables, true),
            params = {
                variables: json_data,// $scope.variables === '---' || $scope.variables === '{}' ? null : $scope.variables,
                name: $scope.name,
                description: $scope.description,
                enabled: $scope.host.enabled,
                inventory: $stateParams.inventory_id
            };
            HostManageService.post(params).then(function(res) {
                // assign the host to current group if not at the root level
                if ($stateParams.group) {
                    HostManageService.associateGroup(res.data, _.last($stateParams.group)).then(function() {
                        $state.go('^.edit', { host_id: res.data.id }, { reload: true });
                    });
                } else {
                    $state.go('^.edit', { host_id: res.data.id }, { reload: true });
                }
            });
        };
    }
];
