/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
 	['$scope', '$state', 'HostsService', 'host', '$rootScope',
 	function($scope, $state, HostsService, host, $rootScope){
        $scope.isSmartInvHost = $state.includes('inventories.editSmartInventory.hosts.edit');
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
 				variables: $scope.host_variables === '---' || $scope.host_variables === '{}' ? null : $scope.host_variables,
 				name: $scope.name,
 				description: $scope.description,
 				enabled: $scope.host.enabled
 			};
                        if (typeof $scope.host.instance_id !== 'undefined') {
                            host.instance_id = $scope.host.instance_id;
                        }
 			HostsService.put(host).then(function(){
 				$state.go('.', null, {reload: true});
 			});

 		};
 		var init = function(){
 			$scope.host = host;
 			$scope.name = host.name;
            $rootScope.breadcrumb.host_name = host.name;
 			$scope.description = host.description;
			$scope.host_variables = host.variables;
 		};

 		init();
 	}];
