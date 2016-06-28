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
                    switch($scope.targetRootGroup){
                        case true:
                            // disassociating group will bubble it to the root group level
                            GroupManageService.disassociateGroup(group.id, _.last($stateParams.group)).then(() => $state.go('^', null, {reload: true}));
                            break;
                        default:
                            // at the root group level, no dissassociation is needed
                            if (!$stateParams.group){
                                GroupManageService.associateGroup(group, $scope.selected.id).then(() => $state.go('^', null, {reload: true}));
                                }
                            else{
                                // unsure if orphaned resources get garbage collected, safe bet is to associate before disassociate
                                GroupManageService.associateGroup(group, $scope.selected.id).then(() => {
                                    GroupManageService.disassociateGroup(group.id, _.last($stateParams.group))
                                    .then(() => $state.go('^', null, {reload: true}));
                                });
                            }
                            break;
                    }
            }
        };
        $scope.toggleTargetRootGroup = function(){
            $scope.selected = !$scope.selected;
            // cannot perform copy operations to root group level
            $scope.submitMode = 'move';
            // toggle off anything currently selected in the list, for clarity
            _.forEach($scope.groups, (item) => {item.checked = null;});
            // disable list selections
            $('#copyMove-list :input').each((idx, el) => {
                $(el).prop('disabled', (idx, value) => !value);
            });
        };
        var init = function(){
        var url = GetBasePath('inventory') + $stateParams.inventory_id + '/groups/';
        url += $stateParams.group ? '?not__id__in=' + group.id + ',' + _.last($stateParams.group) : '?not__id=' + group.id;
        list.basePath = url;
        $scope.atRootLevel = $stateParams.group ? false : true;
        view.inject(list, {
                mode: 'lookup',
                id: 'copyMove-list',
                scope: $scope,
                input_type: 'radio'
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
