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
        $scope.$watchGroup(['groupsSelected', 'hostsSelected'], function(newVals) {
            $scope.adhocCommandTooltip = (newVals[0] || newVals[1]) ? "Run a command on the selected inventory" : "Select an inventory source by clicking the check box beside it. The inventory source can be a single group or host, a selection of multiple hosts, or a selection of multiple groups.";
        });
 	}];
