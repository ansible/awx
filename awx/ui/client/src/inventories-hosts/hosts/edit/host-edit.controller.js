/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
 	['$scope', '$state', 'HostsService', 'host', '$rootScope',
 	function($scope, $state, HostsService, host, $rootScope){
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
        $scope.groupsTab = function(){
            let id = $scope.host.summary_fields.inventory.id;
            $state.go('hosts.edit.nested_groups', {inventory_id: id});
        };
 		$scope.formSave = function(){
 			var host = {
 				id: $scope.host.id,
 				variables: $scope.variables === '---' || $scope.variables === '{}' ? null : $scope.variables,
 				name: $scope.name,
 				description: $scope.description,
 				enabled: $scope.host.enabled
 			};
 			HostsService.put(host).then(function(){
 				$state.go('.', null, {reload: true});
 			});

 		};
 		var init = function(){
 			$scope.host = host.data;
 			$rootScope.breadcrumb.host_name = host.data.name;
            $scope.name = host.data.name;
 			$scope.description = host.data.description;
			$scope.variables = host.data.variables;
 		};

 		init();
 	}];
