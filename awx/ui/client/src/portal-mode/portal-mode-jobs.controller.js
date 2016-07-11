/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export function PortalModeJobsController($scope, $rootScope, GetBasePath, GenerateList, PortalJobsList, SearchInit,
    PaginateInit){

    var list = PortalJobsList,
    view = GenerateList,
    // show user jobs by default
    defaultUrl = GetBasePath('jobs') + '?created_by=' + $rootScope.current_user.id,
    pageSize = 12;

    if ($rootScope.removeJobStatusChange) {
           $rootScope.removeJobStatusChange();
    }
   $rootScope.removeJobStatusChange = $rootScope.$on('JobStatusChange-portal', function() {
       $scope.search('job');
   });

    $scope.iterator = list.iterator;
    $scope.activeFilter = 'user';

    var init = function(sort){
        // We need to explicitly set the lists base path so that tag searching will keep the '?created_by'
        // query param when it's present.  If we don't do this, then tag search will just grab the base
        // path for this list (/api/v1/jobs) and lose the created_by filter
        list.basePath = defaultUrl;

        view.inject(list, {
            id: 'portal-jobs',
            mode: 'edit',
            scope: $scope,
            searchSize: 'col-md-10 col-xs-12'
        });

        SearchInit({
            scope: $scope,
            set: 'jobs',
            list: list,
            url: defaultUrl
        });

        PaginateInit({
            scope: $scope,
            list: list,
            url: defaultUrl,
            pageSize: pageSize
        });
        $scope.search (list.iterator);
        if(sort) {
            // hack to default to descending sort order
            $scope.sort('job','finished');
        }

    };

    $scope.filterUser = function(){
        $scope.activeFilter = 'user';
        defaultUrl = GetBasePath('jobs') + '?created_by=' + $rootScope.current_user.id;
        init(true);
    };

    $scope.filterAll = function(){
        $scope.activeFilter = 'all';
        defaultUrl = GetBasePath('jobs');
        init(true);
    };

    $scope.refresh = function(){
        $scope.search(list.iterator);
    };

    init(true);
}

PortalModeJobsController.$inject = ['$scope', '$rootScope', 'GetBasePath', 'generateList', 'PortalJobsList', 'SearchInit',
    'PaginateInit'];
