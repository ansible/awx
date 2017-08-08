/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'QuerySet', 'InventoryHostsStrings',
    function($scope, qs, InventoryHostsStrings) {
        $scope.hostFilterTags = [];

        $scope.filterTooltip = InventoryHostsStrings.get('smartinventories.TOOLTIP');

        $scope.$watch('hostFilter', function(){
            $scope.hostFilterTags = [];

            if($scope.hostFilter && $scope.hostFilter !== '') {
                let hostFilterCopy = angular.copy($scope.hostFilter);

                let searchParam = hostFilterCopy.host_filter.split('%20and%20');
                delete hostFilterCopy.host_filter;

                $.each(searchParam, function(index, param) {
                    let paramParts = decodeURIComponent(param).split(/=(.+)/);
                    paramParts[0] = paramParts[0].replace(/__icontains(_DEFAULT)?/g, "");
                    paramParts[0] = paramParts[0].replace(/__search(_DEFAULT)?/g, "");
                    let reconstructedSearchString = qs.decodeParam(paramParts[1], paramParts[0]);
                    $scope.hostFilterTags.push(reconstructedSearchString);
                });

                $scope.hostFilterTags = $scope.hostFilterTags.concat(qs.stripDefaultParams(hostFilterCopy));
            }
        });
    }
];
