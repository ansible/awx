/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state', '$stateParams', '$scope', 'ParseVariableString', 'rbacUiControlService', 'ToJSON',
    'ParseTypeChange', 'GroupsService', 'GetChoices', 'GetBasePath', 'CreateSelect2', 'groupData', '$rootScope',
    function($state, $stateParams, $scope, ParseVariableString, rbacUiControlService, ToJSON,
        ParseTypeChange, GroupsService, GetChoices, GetBasePath, CreateSelect2, groupData, $rootScope) {

        init();

        function init() {
            rbacUiControlService.canAdd(GetBasePath('inventory') + $stateParams.inventory_id + "/groups")
                .then(function(canAdd) {
                $scope.canAdd = canAdd;
            });

            $scope = angular.extend($scope, groupData);

            $rootScope.breadcrumb.group_name = groupData.name;

            $scope.$watch('summary_fields.user_capabilities.edit', function(val) {
                $scope.canAdd = val;
            });

            // init codemirror(s)
            $scope.group_variables = $scope.variables === null || $scope.variables === '' ? '---' : ParseVariableString($scope.variables);
            $scope.parseType = 'yaml';
            $scope.envParseType = 'yaml';


            ParseTypeChange({
                scope: $scope,
                field_id: 'group_group_variables',
                variable: 'group_variables',
                readOnly: !$scope.summary_fields.user_capabilities.edit
            });
        }

        $scope.formCancel = function() {
            $state.go('^');
        };

        $scope.formSave = function() {
            var json_data;
            json_data = ToJSON($scope.parseType, $scope.group_variables, true);
            // group fields
            var group = {
                variables: json_data,
                name: $scope.name,
                description: $scope.description,
                inventory: $scope.inventory,
                id: groupData.id
            };
            GroupsService.put(group).then(() => $state.go($state.current, null, { reload: true }));
        };

    }
];
