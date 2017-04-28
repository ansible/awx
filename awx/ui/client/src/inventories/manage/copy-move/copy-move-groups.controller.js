/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$scope', '$state', '$stateParams', 'GroupManageService', 'CopyMoveGroupList', 'group', 'Dataset',
    function($scope, $state, $stateParams, GroupManageService, CopyMoveGroupList, group, Dataset){
        var list = CopyMoveGroupList;

        $scope.item = group;
        $scope.submitMode = $stateParams.groups === undefined ? 'move' : 'copy';

        $scope.updateSelected = function(selectedGroup) {
            $scope.selected = angular.copy(selectedGroup);
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

        function init(){
            $scope.atRootLevel = $stateParams.group ? false : true;

            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
        }

        init();
    }];
