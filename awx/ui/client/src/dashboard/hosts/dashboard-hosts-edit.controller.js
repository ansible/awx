/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
 	['$scope', '$state', '$stateParams', 'DashboardHostsForm', 'GenerateForm', 'ParseTypeChange', 'DashboardHostService', 'host',
 	function($scope, $state, $stateParams, DashboardHostsForm, GenerateForm, ParseTypeChange, DashboardHostService, host){
 		$scope.parseType = 'yaml';
 		$scope.formCancel = function(){
 			$state.go('^', null, {reload: true});
 		};
 		$scope.toggleHostEnabled = function(){
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
 			$scope.host = host.data;
 			$scope.name = host.data.name;
 			$scope.description = host.data.description;
 			$scope.variables = host.data.variables === '' ? '---' : host.data.variables;
        	ParseTypeChange({
        		scope: $scope,
        		field_id: 'host_variables',
        		variable: 'variables',
        	});
 		};

 		init();
 	}];
