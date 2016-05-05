/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
 	['$scope', '$state', '$stateParams', 'DashboardHostsForm', 'GenerateForm', 'ParseTypeChange', 'DashboardHostService', 'host',
 	function($scope, $state, $stateParams, DashboardHostsForm, GenerateForm, ParseTypeChange, DashboardHostService, host){
 		var generator = GenerateForm,
 			form = DashboardHostsForm;
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
 				variables: $scope.extraVars === '---' || $scope.extraVars === '{}' ? null : $scope.extraVars,
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
 			$scope.extraVars = host.variables === '' ? '---' : host.variables;
 			generator.inject(form, {mode: 'edit', related: false, scope: $scope});
     		$scope.extraVars = $scope.host.variables === '' ? '---' : $scope.host.variables;
    		$scope.name = host.name;
 			$scope.description = host.description;
        	ParseTypeChange({
        		scope: $scope,
        		field_id: 'host_variables',
        		variable: 'extraVars',
        	});
 		};

 		init();
 	}];
