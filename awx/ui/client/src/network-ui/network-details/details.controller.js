/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
 	['$scope', '$state', '$stateParams', 'GenerateForm', 'ParseTypeChange', 'HostsService', '$rootScope',
 	function($scope, $state, $stateParams, GenerateForm, ParseTypeChange, HostsService, $rootScope){

        $scope.parseType = 'yaml';
 		$scope.formCancel = function(){
            $scope.$parent.$$childTail.closeDetailsPanel();
 		};

 		$scope.formSave = function(){
 			var host = {
 				id: $scope.item.id,
 				variables: $scope.variables === '---' || $scope.variables === '{}' ? null : $scope.variables,
 				name: $scope.item.name,
 				description: $scope.item.description,
 				enabled: $scope.item.enabled
 			};
 			HostsService.put(host).then(function(response){
                $scope.saveConfirmed = true;
                if(_.has(response, "data")){
                    $scope.$parent.$broadcast('hostUpdateSaved', response.data);
                }
                setTimeout(function(){
                    $scope.saveConfirmed = false;
                }, 3000);
 			});

 		};

        $scope.$parent.$on('showDetails', (e, data, canAdd) => {
            if (!_.has(data, 'host_id')) {
                $scope.item = data;
                $scope.canAdd = canAdd;
            } else {
                $scope.item = data;
            }
        });

        $scope.$watch('item', function(){
            init();
        });

 		var init = function(){
            if($scope.item && $scope.item.host_id){
    			$scope.variables = getVars($scope.item.variables);
            	ParseTypeChange({
            		scope: $scope,
            		field_id: 'network_host_variables',
            		variable: 'variables',
            	});
            }

 		};

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

 		// init();
 	}];
