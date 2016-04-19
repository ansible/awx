/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default 
 	['$stateParams', '$scope', '$rootScope', '$state', 'Wait',
 	 'JobDetailService', 'CreateSelect2', 'hosts',
 	function($stateParams, $scope, $rootScope, $state, Wait,
 	 JobDetailService, CreateSelect2, hosts){

 	// pagination not implemented yet, but it'll depend on this
 	$scope.page_size = $stateParams.page_size;

 	$scope.processEventStatus = JobDetailService.processEventStatus;
 	$scope.activeFilter = $stateParams.filter || null;

 	$scope.search = function(){
 		Wait('start');
 		if ($scope.searchStr == undefined){
 			return
 		}
 		//http://docs.ansible.com/ansible-tower/latest/html/towerapi/intro.html#filtering
 		// SELECT WHERE host_name LIKE str OR WHERE play LIKE str OR WHERE task LIKE str AND host_name NOT ""
 		// selecting non-empty host_name fields prevents us from displaying non-runner events, like playbook_on_task_start
	 	JobDetailService.getRelatedJobEvents($stateParams.id, {
	 		or__host_name__icontains: $scope.searchStr,
	 		or__play__icontains: $scope.searchStr,
	 		or__task__icontains: $scope.searchStr,
	 		not__host_name: "" ,
	 		page_size: $scope.pageSize})
	 			.success(function(res){
	 				$scope.results = res.results;
	 				Wait('stop')
	 	});
 	};

 	$scope.filters = ['all', 'changed', 'failed', 'ok', 'unreachable', 'skipped'];

 	var filter = function(filter){
 		Wait('start');

 		if (filter == 'all'){
	 		return JobDetailService.getRelatedJobEvents($stateParams.id, {
	 			host_name: $stateParams.hostName,
	 			page_size: $scope.pageSize})
	 			.success(function(res){
	 				$scope.results = res.results;
	 				Wait('stop');
	 		});
 		}
 		// handle runner cases
 		if (filter == 'skipped'){
 			return JobDetailService.getRelatedJobEvents($stateParams.id, {
 				host_name: $stateParams.hostName, 
 				event: 'runner_on_skipped'})
 				.success(function(res){
 					$scope.results = res.results;
 					Wait('stop');
 				});
 		}
 		if (filter == 'unreachable'){
  			return JobDetailService.getRelatedJobEvents($stateParams.id, {
 				host_name: $stateParams.hostName, 
 				event: 'runner_on_unreachable'})
 				.success(function(res){
 					$scope.results = res.results;
 					Wait('stop');
 				});
 		}
 		if (filter == 'ok'){
  			return JobDetailService.getRelatedJobEvents($stateParams.id, {
 				host_name: $stateParams.hostName, 
 				or__field__event: 'runner_on_ok',
 				or__field__event: 'runner_on_ok_async',  
 				changed: false
 				})
 				.success(function(res){
 					$scope.results = res.results;
 					Wait('stop');
 				}); 			
 		}
  		// handle convience properties .changed .failed
 		if (filter == 'changed'){
  			return JobDetailService.getRelatedJobEvents($stateParams.id, {
 				host_name: $stateParams.hostName, 
 				changed: true})
 				.success(function(res){
 					$scope.results = res.results;
 					Wait('stop');
 				}); 			
 		}
 		if (filter == 'failed'){
  			return JobDetailService.getRelatedJobEvents($stateParams.id, {
 				host_name: $stateParams.hostName,
 				failed: true})
 				.success(function(res){
 					$scope.results = res.results;
 					Wait('stop');
 				}); 			
 		} 		
 	};

 	// watch select2 for changes
 	$('.HostEvents-select').on("select2:select", function (e) {
 	 	filter($('.HostEvents-select').val());
 	});

 	var init = function(){
 		$scope.hostName = $stateParams.hostName;
 		// create filter dropdown
 		CreateSelect2({
 			element: '.HostEvents-select',
 			multiple: false
 		});
 		// process the filter if one was passed
 		if ($stateParams.filter){
 			Wait('start');
 			filter($stateParams.filter).success(function(res){
	 				$scope.results = res.results;
	 				Wait('stop');
	 				$('#HostEvents').modal('show');
	 		});;
 		}
 		else{
 			$scope.results = hosts.data.results;
	 		$('#HostEvents').modal('show');
 		}	
 	};


 	init();

 	}];