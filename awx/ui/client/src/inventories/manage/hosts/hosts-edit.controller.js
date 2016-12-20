/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
     ['$state', '$stateParams', '$scope', 'HostForm', 'ParseTypeChange', 'HostManageService', 'host', 'ToJSON',
     function($state, $stateParams, $scope, HostForm, ParseTypeChange, HostManageService, host, ToJSON){

        init();

        function init(){
            $scope.$watch('host.summary_fields.user_capabilities.edit', function(val) {
                if (val === false) {
                    $scope.canAdd = false;
                }
            });

            $scope.parseType = 'yaml';
            $scope.host = host;
            $scope.variables = getVars(host.variables);
            $scope.name = host.name;
            $scope.description = host.description;

            ParseTypeChange({
                scope: $scope,
                field_id: 'host_variables',
            });
        }

        // Adding this function b/c sometimes extra vars are returned to the
        // UI as a string (ex: "foo: bar"), and other times as a
        // json-object-string (ex: "{"foo": "bar"}"). CodeMirror wouldn't know
        // how to prettify the latter. The latter occurs when host vars were
        // system generated and not user-input (such as adding a cloud host);
        function getVars(str){

            // Quick function to test if the host vars are a json-object-string,
            // by testing if they can be converted to a JSON object w/o error. 
            function IsJsonString(str) {
                try {
                    JSON.parse(str);
                } catch (e) {
                    return false;
                }
                return true;
            }

            if(str === ''){
                return '---';
            }
            else if(IsJsonString(str)){
                str = JSON.parse(str);
                return jsyaml.safeDump(str);
            }
            else if(!IsJsonString(str)){
                return str;
            }
        }

        $scope.formCancel = function(){
            $state.go('^');
        };
        $scope.toggleHostEnabled = function(){
            $scope.host.enabled = !$scope.host.enabled;
        };
        $scope.formSave = function(){
            var json_data = ToJSON($scope.parseType, $scope.variables, true),
            host = {
                id: $scope.host.id,
                variables: json_data,
                name: $scope.name,
                description: $scope.description,
                enabled: $scope.host.enabled
            };
            HostManageService.put(host).then(function(){
                $state.go($state.current, null, {reload: true});
            });
        };
    }];
