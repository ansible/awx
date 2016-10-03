/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$state', '$stateParams', '$scope', 'HostForm', 'ParseTypeChange', 'GenerateForm', 'HostManageService', 'host', 'ParseVariableString',
    function($state, $stateParams, $scope, HostForm, ParseTypeChange, GenerateForm, HostManageService, host, ParseVariableString){
        var generator = GenerateForm,
            form = HostForm;
        $scope.parseType = 'yaml';
        $scope.formCancel = function(){
            $state.go('^');
        };
        $scope.toggleHostEnabled = function(){
            $scope.host.enabled = !$scope.host.enabled;
        };
        $scope.formSave = function(){
            var host = {
                id: $scope.host.id,
                variables: $scope.variables === '---' || $scope.variables === '{}' ? null : $scope.variables,
                name: $scope.name,
                description: $scope.description,
                enabled: $scope.host.enabled
            };
            HostManageService.put(host).then(function(){
                $state.go($state.current, null, {reload: true});
            });
        };
        var init = function(){
            $scope.host = host;
            generator.inject(form, {mode: 'edit', related: false, id: 'Inventory-hostManage--panel', scope: $scope});
            $scope.variables = host.variables === '' ? '---' : ParseVariableString(host.variables);
            $scope.name = host.name;
            $scope.description = host.description;
            ParseTypeChange({
                scope: $scope,
                field_id: 'host_variables'
            });
        };
        init();
    }];
