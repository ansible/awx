/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 export default
 	['$scope', '$state', function($scope, $state){
 		$scope.groupsSelected = false;
 		$scope.hostsSelected = false;
 		$scope.hostsSelectedItems = [];
 		$scope.groupsSelectedItems = [];
 		$scope.setAdhocPattern = function(){
 			var pattern = _($scope.groupsSelectedItems)
 				.concat($scope.hostsSelectedItems)
 				.map(function(item){
 					return item.name;
 				}).value().join(':');
 			$state.go('inventoryManage.adhoc', {pattern: pattern});
 		};
 	}];