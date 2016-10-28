/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export function PortalModeJobsController($scope, $rootScope, $state, $stateParams, qs, GetBasePath, PortalJobsList, Dataset) {

    var list = PortalJobsList;

    $scope.$on('ws-jobs', function() {
        // @issue: OLD SEARCH
        //$scope.search('job');
    });
    if ($rootScope.removeJobStatusChange) {
        $rootScope.removeJobStatusChange();
    }
    $rootScope.removeJobStatusChange = $rootScope.$on('JobStatusChange-portal', function() {
        $state.go('.', null, { reload: true });
    });

    init();

    function init() {
        // search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        $scope.iterator = list.iterator;
    }

    $scope.refresh = function() {
        $state.go('.', null, {reload: true});
    };
}

PortalModeJobsController.$inject = ['$scope', '$rootScope', '$state', '$stateParams', 'QuerySet', 'GetBasePath', 'PortalJobsList', 'jobsDataset'];
