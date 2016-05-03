/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$state', '$stateParams', '$scope', 'HostForm', 'ParseTypeChange', 'GenerateForm', 'ManageHostsService',
    function($state, $stateParams, $scope, HostForm, ParseTypeChange, GenerateForm, ManageHostsService){
        var generator = GenerateForm,
            form = HostForm;
        $scope.parseType = 'yaml';
        $scope.extraVars = '---';
        $scope.formCancel = function(){
            $state.go('^', null, {reload: true});
        };
        $scope.toggleEnabled = function(){
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
            ManageHostsService.post(params).then(function(){
                $state.go('^', null, {reload: true});
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
