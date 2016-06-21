/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    ['$state', '$stateParams', '$scope', 'inventoryData', 'breadCrumbData', function($state, $stateParams, $scope, inventoryData, breadCrumbData){
        // process result data into the same order specified in the traversal path
        $scope.groups = _.sortBy(breadCrumbData, function(item){
            var index = _.indexOf($stateParams.group, item.id);
            return (index === -1) ? $stateParams.group.length : index;
        });
        $scope.inventory = inventoryData;
        $scope.state = $state;
        // slices the group stack at $index to supply new group params to $state.go()
        $scope.goToGroup = function(index){
            var group = $stateParams.group.slice(0, index);
            $state.go('inventoryManage', {group: group}, {reload: true});
        };
        $scope.isRootState = function(){
            return $state.current.name === 'inventoryManage';
        };
        $scope.goToInventory = function(){
            $state.go('inventoryManage', {group: undefined}, {reload: true});
        };
    }];
