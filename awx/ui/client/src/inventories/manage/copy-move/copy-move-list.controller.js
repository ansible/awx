/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$scope', 'CopyMoveGroupList', 'Dataset',
    function($scope, list, Dataset){
        init();

        function init() {
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            $scope.$watch('groups', function(){
                if($scope.selectedGroup){
                    $scope.groups.forEach(function(row, i) {
                        if(row.id === $scope.selectedGroup.id) {
                            $scope.groups[i].checked = 1;
                        }
                        else {
                            $scope.groups[i].checked = 0;
                        }
                    });
                }
            });
        }

        $scope.toggle_row = function(id) {
            // toggle off anything else currently selected
            _.forEach($scope.groups, (item) => {
                if(item.id === id) {
                    item.checked = 1;
                    $scope.selectedGroup = item;
                    $scope.updateSelected(item);
                }
                else {
                    item.checked = null;
                }
            });
        };
    }];
