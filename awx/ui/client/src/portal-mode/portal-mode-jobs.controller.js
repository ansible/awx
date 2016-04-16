/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export function PortalModeJobsController($scope, $state, $rootScope, GetBasePath, GenerateList, PortalJobsList, SearchInit,
	PaginateInit){

	var list = PortalJobsList,
	view = GenerateList,
	// show user jobs by default
	defaultUrl = GetBasePath('jobs') + '?created_by=' + $rootScope.current_user.id,
	pageSize = 12;

	$scope.iterator = list.iterator;
	$scope.activeFilter = 'user';

	var init = function(){
		view.inject(list, {
			id: 'portal-jobs',
			mode: 'edit',
			scope: $scope,
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
	};


	$scope.filterUser = function(){
		$scope.activeFilter = 'user';
		defaultUrl = GetBasePath('jobs') + '?created_by=' + $rootScope.current_user.id;
		init();
	};

	$scope.filterAll = function(){
		$scope.activeFilter = 'all';
		defaultUrl = GetBasePath('jobs');
		init();
	};

	init();
}

PortalModeJobsController.$inject = ['$scope', '$state', '$rootScope', 'GetBasePath', 'generateList', 'PortalJobsList', 'SearchInit',
	'PaginateInit']