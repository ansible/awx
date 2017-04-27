/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state', '$stateParams', '$scope', 'GroupForm',
    'ParseTypeChange', 'GenerateForm', 'inventoryData', 'GroupManageService',
    'GetChoices', 'GetBasePath', 'CreateSelect2', 'GetSourceTypeOptions',
    'rbacUiControlService', 'ToJSON',
    function($state, $stateParams, $scope, GroupForm,  ParseTypeChange,
        GenerateForm, inventoryData, GroupManageService, GetChoices,
        GetBasePath, CreateSelect2, GetSourceTypeOptions, rbacUiControlService,
        ToJSON) {

        let form = GroupForm;
        init();

        function init() {
            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);

            rbacUiControlService.canAdd(GetBasePath('inventory') + $stateParams.inventory_id + "/groups")
                .then(function(canAdd) {
                    $scope.canAdd = canAdd;
                });
            $scope.parseType = 'yaml';
            $scope.envParseType = 'yaml';
            ParseTypeChange({
                scope: $scope,
                field_id: 'group_variables',
                variable: 'variables',
            });
        }

        $scope.formCancel = function() {
            $state.go('^');
        };

        $scope.formSave = function() {
            var json_data;
            json_data = ToJSON($scope.parseType, $scope.variables, true);

            var group = {
                variables: json_data,
                name: $scope.name,
                description: $scope.description,
                inventory: inventoryData.id
            };

            GroupManageService.post(group).then(res => {
                if ($stateParams.group_id) {
                    return GroupManageService.associateGroup(res.data, $stateParams.group_id)
                        .then(() => $state.go('^', null, { reload: true }));
                } else {
                    $state.go('^.edit', { group_id: res.data.id }, { reload: true });
                }
            });

        };
    }
];
