/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state', '$stateParams', '$scope', 'NestedGroupForm',
    'ParseTypeChange', 'GenerateForm', 'inventoryData', 'GroupsService',
    'GetChoices', 'GetBasePath', 'CreateSelect2',
    'rbacUiControlService', 'ToJSON', 'canAdd',
    function($state, $stateParams, $scope, NestedGroupForm,  ParseTypeChange,
        GenerateForm, inventoryData, GroupsService, GetChoices,
        GetBasePath, CreateSelect2, rbacUiControlService,
        ToJSON, canAdd) {

        let form = NestedGroupForm;
        init();

        function init() {
            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);
            $scope.canAdd = canAdd;
            $scope.parseType = 'yaml';
            $scope.envParseType = 'yaml';
            ParseTypeChange({
                scope: $scope,
                field_id: 'nested_group_nested_group_variables',
                variable: 'nested_group_variables',
            });
        }

        $scope.formCancel = function() {
            $state.go('^');
        };

        $scope.formSave = function() {
            var json_data;
            json_data = ToJSON($scope.parseType, $scope.nested_group_variables, true);

            var group = {
                variables: json_data,
                name: $scope.name,
                description: $scope.description,
                inventory: inventoryData.id
            };

            GroupsService.post(group).then(res => {
                if ($stateParams.group_id && _.has(res, 'data')) {
                    return GroupsService.associateGroup(res.data, $stateParams.group_id)
                        .then(() => $state.go('^', null, { reload: true }));
                } else if(_.has(res, 'data.id')){
                    $state.go('^.edit', { group_id: res.data.id }, { reload: true });
                }
            });

        };
    }
];
