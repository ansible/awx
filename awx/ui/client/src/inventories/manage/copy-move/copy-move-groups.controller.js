/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$scope', '$state', '$stateParams', 'generateList', 'SearchInit', 'PaginateInit', 'GroupManageService', 'GetBasePath', 'CopyMoveGroupList', 'group',
    function($scope, $state, $stateParams, GenerateList, SearchInit, PaginateInit, GroupManageService, GetBasePath, CopyMoveGroupList, group){
        var list = CopyMoveGroupList,
            view = GenerateList;
        $scope.item = group;
        $scope.submitMode = $stateParams.groups === undefined ? 'move' : 'copy';
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
                    GroupManageService.associateGroup(group, $scope.selected.id).then(() => $state.go('^', null, {reload: true}));
                    break;
                case 'move':
                    // at the root group level, no dissassociation is needed
                    if (!$stateParams.group){
                        GroupManageService.associateGroup(group, $scope.selected.id).then(() => $state.go('^', null, {reload: true}));
                        }
                    else{
                        // unsure if orphaned resources get garbage collected, safe bet is to associate before disassociate
                        GroupManageService.associateGroup(group, $scope.selected.id).then(() => {
                            GroupManageService.disassociateGroup(group, _.last($stateParams.group))
                            .then(() => $state.go('^', null, {reload: true}));
                        });                        
                    }
                    break;
            }
        };
        var init = function(){
        var url = GetBasePath('inventory') + $stateParams.inventory_id + '/groups/';
        url += $stateParams.group ? '?not__id__in=' + group.id + ',' + _.last($stateParams.group) : '?not__id=' + group.id;
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
            // remove the current group from list
        };
        init();
    }];