/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope',
    function ($scope) {
        $scope.unselectSelectedRow = function(index) {

            angular.forEach($scope.availableRows, function(value) {
                if(value.id === $scope.selectedRows[index].id) {
                    value.isSelected = false;
                }
            });

            $scope.selectedRows.splice(index, 1);

        };
    }
];
