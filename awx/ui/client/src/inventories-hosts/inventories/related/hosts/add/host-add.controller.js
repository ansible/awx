/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state', '$stateParams', '$scope', 'RelatedHostsFormDefinition',
                'GenerateForm', 'HostsService', 'GetBasePath', 'ToJSON', 'canAdd',
                function($state, $stateParams, $scope, RelatedHostsFormDefinition,
                         GenerateForm, HostsService, GetBasePath, ToJSON, canAdd) {

        init();

        function init() {
            $scope.canAdd = canAdd;
            $scope.host = { enabled: true };
            // apply form definition's default field values
            GenerateForm.applyDefaults(RelatedHostsFormDefinition, $scope);
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
            var json_data = ToJSON($scope.parseType, $scope.host_variables, true),
            params = {
                variables: json_data,// $scope.variables === '---' || $scope.variables === '{}' ? null : $scope.variables,
                name: $scope.name,
                description: $scope.description,
                enabled: $scope.host.enabled,
                inventory: $stateParams.inventory_id
            };
            HostsService.post(params).then(function(res) {
                $state.go('^.edit', { host_id: res.data.id }, { reload: true });
            })
            .catch(function(){});
        };
    }
];
