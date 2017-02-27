/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export function PortalModeJobsController($scope, $rootScope, $state, $stateParams, qs, GetBasePath, PortalJobsList, Dataset) {

    var list = PortalJobsList;

    $scope.$on('ws-jobs', function() {
        let path = GetBasePath(list.basePath) || GetBasePath(list.name);
        qs.search(path, $state.params[`${list.iterator}_search`])
        .then(function(searchResponse) {
            $scope[`${list.iterator}_dataset`] = searchResponse.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
        });
    });

    init();

    function init(data) {
        let d = (!data) ? Dataset : data;
        // search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = d.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        $scope.iterator = list.iterator;
    }

    $scope.$on('filterPortalJobs', function(e, data){
        init(data);
    });

    $scope.refresh = function() {
        $state.go('.', null, {reload: true});
    };
}

PortalModeJobsController.$inject = ['$scope', '$rootScope', '$state', '$stateParams', 'QuerySet', 'GetBasePath', 'PortalJobsList', 'jobsDataset'];
