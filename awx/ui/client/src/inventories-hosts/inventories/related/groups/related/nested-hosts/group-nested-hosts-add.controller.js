/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state', '$stateParams', '$scope', 'RelatedHostsFormDefinition', 'ParseTypeChange',
                'GenerateForm', 'HostsService', 'ToJSON', 'canAdd', 'GroupsService',
                function($state, $stateParams, $scope, RelatedHostsFormDefinition, ParseTypeChange,
                         GenerateForm, HostsService, ToJSON, canAdd, GroupsService) {

        init();

        function init() {
            $scope.canAdd = canAdd;
            $scope.parseType = 'yaml';
            $scope.host = { enabled: true };
            // apply form definition's default field values
            GenerateForm.applyDefaults(RelatedHostsFormDefinition, $scope);

            ParseTypeChange({
                scope: $scope,
                field_id: 'host_host_variables',
                variable: 'host_variables',
                parse_variable: 'parseType'
            });
        }
        $scope.formCancel = function() {
            $state.go('^');
        };
        $scope.toggleHostEnabled = function() {
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
                return GroupsService.associateHost(res.data, $stateParams.group_id)
                    .then(() => $state.go('^', null, { reload: true }));
            });
        };
    }
];
