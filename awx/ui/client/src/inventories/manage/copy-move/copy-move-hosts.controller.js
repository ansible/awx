/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$scope', '$state', '$stateParams', 'generateList', 'SearchInit', 'PaginateInit', 'HostManageService', 'GetBasePath', 'CopyMoveGroupList', 'host',
    function($scope, $state, $stateParams, GenerateList, SearchInit, PaginateInit, HostManageService, GetBasePath, CopyMoveGroupList, host){
        var list = CopyMoveGroupList,
            view = GenerateList;
        $scope.item = host;
        $scope.submitMode = 'copy';
        $scope['toggle_'+ list.iterator] = function(id){
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
        var init = function(){
            var url = GetBasePath('inventory') + $stateParams.inventory_id + '/groups/';
            list.basePath = url;
            view.inject(list, {
                mode: 'lookup',
                id: 'copyMove-list',
                scope: $scope
            });
            SearchInit({
                scope: $scope,
                set: list.name,
                list: list,
                url: url
            });
            PaginateInit({
                scope: $scope,
                list: list,
                url : url,
                mode: 'lookup'
            });
            $scope.search(list.iterator, null, true, false);
        };
        init();
    }];
