/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$scope', '$state', '$stateParams', 'HostManageService', 'CopyMoveGroupList', 'host', 'Dataset', '$rootScope',
    function($scope, $state, $stateParams, HostManageService, CopyMoveGroupList, host, Dataset, $rootScope){
        let list = CopyMoveGroupList;

        let init = function(){
            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            $scope.item = host;
            $rootScope.breadcrumb.copyMoveName = host.name;
            $scope.submitMode = 'copy';
        };

        init();

        $scope.toggle_row = function(id){
            // toggle off anything else currently selected
            _.forEach($scope.groups, (item) => {return item.id === id ? item.checked = 1 : item.checked = null;});
            // yoink the currently selected thing
            $scope.selected = _.find($scope.groups, (item) => {return item.id === id;});
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
    }];
