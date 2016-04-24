/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
	['$scope', '$state', '$stateParams', 'Rest', 'GetBasePath', 'DashboardHostsList', 
	'generateList', 'PaginateInit', 'SetStatus', 'DashboardHostsService', 'hosts',  
	function($scope, $state, $stateParams, Rest, GetBasePath, DashboardHostsList, GenerateList, PaginateInit, SetStatus, DashboardHostsService, hosts){
		var generator = GenerateList,
			list = DashboardHostsList,
			defaultUrl = GetBasePath('hosts');
		$scope.editHost = function(id){
			$state.go('dashboardHosts.edit', {id: id});
		};
		$scope.toggleHostEnabled = function(host){
			DashboardHostsService.setHostStatus(host, !host.enabled)
			.then(function(res){
				var index = _.findIndex($scope.hosts, function(o) {return o.id === res.data.id;});
				$scope.hosts[index].enabled = res.data.enabled;
			});
		};
		var setJobStatus = function(){
			_.forEach($scope.hosts, function(value, key){
				SetStatus({
					scope: $scope,
					host: value
				});
			});
		};
		var init = function(){
				$scope.list = list;
				$scope.host_active_search = false;
				$scope.host_total_rows = hosts.length;
				$scope.hosts = hosts;
				setJobStatus();
				generator.inject(list, {mode: 'edit', scope: $scope});
				PaginateInit({
					scope: $scope,
					list: list,
					url: defaultUrl
				});
				console.log($scope)
				$scope.hostLoading = false;
		};
		init();
	}];