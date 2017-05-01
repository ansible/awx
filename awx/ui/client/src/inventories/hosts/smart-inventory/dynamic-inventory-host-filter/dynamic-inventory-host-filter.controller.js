/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'QuerySet',
    function($scope, qs) {
        $scope.hostFilterTags = [];

        $scope.$watch('hostFilter', function(){
            $scope.hostFilterTags = qs.stripDefaultParams($scope.hostFilter);
        });
    }
];
