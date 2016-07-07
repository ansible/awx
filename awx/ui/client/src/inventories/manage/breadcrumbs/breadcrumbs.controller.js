/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    ['$state', '$stateParams', '$scope', '$rootScope', 'inventoryData', 'breadCrumbData', function($state, $stateParams, $scope, $rootScope, inventoryData, breadCrumbData){
        // process result data into the same order specified in the traversal path
        $scope.groups = _.sortBy(breadCrumbData, function(item){
            var index = _.indexOf($stateParams.group, item.id);
            return (index === -1) ? $stateParams.group.length : index;
        });
        $scope.inventory = inventoryData;
        $scope.currentState = $state.current.name;
        // The ncy breadcrumb directive will look at this attribute when attempting to bind to the correct scope.
        // In this case, we don't want to incidentally bind to this scope when editing a host or a group.  See:
        // https://github.com/ncuillery/angular-breadcrumb/issues/42 for a little more information on the
        // problem that this solves.
        $scope.ncyBreadcrumbIgnore = true;
        // slices the group stack at $index to supply new group params to $state.go()
        $scope.goToGroup = function(index){
            var group = $stateParams.group.slice(0, index);
            $state.go('inventoryManage', {group: group}, {reload: true});
        };
        $scope.goToInventory = function(){
            $state.go('inventoryManage', {group: undefined}, {reload: true});
        };

        var cleanUpStateChangeListener = $rootScope.$on('$stateChangeSuccess', function(event, toState){
            $scope.currentState = toState.name;
        });

        // Remove the listener when the scope is destroyed to avoid a memory leak
        $scope.$on('$destroy', function() {
            cleanUpStateChangeListener();
        });
    }];
