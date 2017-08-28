/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'QuerySet', 'InventoryHostsStrings',
    function($scope, qs, InventoryHostsStrings) {
        $scope.hostFilterTags = [];

        $scope.filterTooltip = $scope.fieldIsDisabled ? '' : InventoryHostsStrings.get('smartinventories.TOOLTIP');

        $scope.$watch('hostFilter', function(){
            $scope.hostFilterTags = [];

            if($scope.hostFilter && $scope.hostFilter !== '') {
                let hostFilterCopy = angular.copy($scope.hostFilter);

                let searchParam = hostFilterCopy.host_filter.split('%20and%20');
                delete hostFilterCopy.host_filter;

                $.each(searchParam, function(index, param) {
                    let paramParts = decodeURIComponent(param).split(/=(.+)/);
                    $scope.hostFilterTags.push(qs.decodeParam(paramParts[1], paramParts[0]));
                });

                $scope.hostFilterTags = $scope.hostFilterTags.concat(qs.stripDefaultParams(hostFilterCopy));
            }
        });
    }
];
