/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$state', '$stateParams', '$scope', 'HostForm', 'ParseTypeChange', 'GenerateForm', 'HostManageService',
    function($state, $stateParams, $scope, HostForm, ParseTypeChange, GenerateForm, HostManageService){
        var generator = GenerateForm,
            form = HostForm;
        $scope.parseType = 'yaml';
        $scope.extraVars = '---';
        $scope.formCancel = function(){
            $state.go('^');
        };
        $scope.toggleHostEnabled = function(){
            $scope.host.enabled = !$scope.host.enabled;
        };
        $scope.formSave = function(){
            var params = {
                variables: $scope.extraVars === '---' || $scope.extraVars === '{}' ? null : $scope.extraVars,
                name: $scope.name,
                description: $scope.description,
                enabled: $scope.host.enabled,
                inventory: $stateParams.inventory_id
            };
            HostManageService.post(params).then(function(res){
                // assign the host to current group if not at the root level
                if ($stateParams.group){
                    HostManageService.associateGroup(res.data, _.last($stateParams.group)).then(function(){
                        $state.go('inventoryManage', null, {reload: true});
                    });
                }
                else{
                    $state.go('inventoryManage', null, {reload: true});
                }
            });
        };
        var init = function(){
            $scope.host = {enabled: true};
            generator.inject(form, {mode: 'add', related: false, id: 'Inventory-hostManage--panel', scope: $scope});
            ParseTypeChange({
                scope: $scope,
                field_id: 'host_variables',
                variable: 'extraVars',
            });
        };
        init();
    }];
