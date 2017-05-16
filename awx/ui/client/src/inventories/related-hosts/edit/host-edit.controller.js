/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
 	['$scope', '$state', '$stateParams', 'DashboardHostsForm', 'GenerateForm', 'ParseTypeChange', 'DashboardHostService', 'host', '$rootScope',
 	function($scope, $state, $stateParams, DashboardHostsForm, GenerateForm, ParseTypeChange, DashboardHostService, host, $rootScope){
 		$scope.parseType = 'yaml';
 		$scope.formCancel = function(){
 			$state.go('^', null, {reload: true});
 		};
 		$scope.toggleHostEnabled = function(){
			if ($scope.host.has_inventory_sources){
				return;
			}
 			$scope.host.enabled = !$scope.host.enabled;
 		};
 		$scope.toggleEnabled = function(){
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
 			DashboardHostService.putHost(host).then(function(){
 				$state.go('^', null, {reload: true});
 			});

 		};
 		var init = function(){
 			$scope.host = host;
 			$scope.name = host.name;
            $rootScope.breadcrumb.host_name = host.name;
 			$scope.description = host.description;
			$scope.variables = getVars(host.variables);
        	ParseTypeChange({
        		scope: $scope,
        		field_id: 'host_variables',
        		variable: 'variables',
        	});
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

 		init();
 	}];
