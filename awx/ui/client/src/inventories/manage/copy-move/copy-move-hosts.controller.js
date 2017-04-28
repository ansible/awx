/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$scope', '$state', '$stateParams', 'HostManageService', 'CopyMoveGroupList', 'host', 'Dataset',
    function($scope, $state, $stateParams, HostManageService, CopyMoveGroupList, host, Dataset){
        var list = CopyMoveGroupList;

        $scope.item = host;
        $scope.submitMode = 'copy';
        
        $scope.updateSelected = function(selectedGroup) {
            $scope.selected = angular.copy(selectedGroup);
        };
        $scope.formCancel = function(){
            $state.go('^');
        };
        $scope.formSave = function(){
            switch($scope.submitMode) {
                case 'copy':
                    HostManageService.associateGroup(host, $scope.selected.id).then(() => $state.go('^'));
                    break;
                case 'move':
                    // at the root group level, no dissassociation is needed
                    if (!$stateParams.group){
                        HostManageService.associateGroup(host, $scope.selected.id).then(() => $state.go('^', null, {reload: true}));
                        }
                    else{
                        HostManageService.associateGroup(host, $scope.selected.id).then(() => {
                            HostManageService.disassociateGroup(host, _.last($stateParams.group))
                            .then(() => $state.go('^', null, {reload: true}));
                        });
                    }
                    break;
            }
        };
        var init = function(){
            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        };
        init();
    }];
