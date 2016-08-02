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
 		//http://docs.ansible.com/ansible-tower/latest/html/towerapi/intro.html#filtering
 		// SELECT WHERE host_name LIKE str OR WHERE play LIKE str OR WHERE task LIKE str AND host_name NOT ""
 		// selecting non-empty host_name fields prevents us from displaying non-runner events, like playbook_on_task_start
 		var params = {
	 		host_name: $scope.hostName,
 		};
 		if ($scope.searchStr && $scope.searchStr !== ''){
 	 		params.or__play__icontains = encodeURIComponent($scope.searchStr);
	 		params.or__task__icontains = encodeURIComponent($scope.searchStr);
 		}

 		switch($scope.activeFilter){
 			case 'skipped':
 				params.event = 'runner_on_skipped';
 				break;
 			case 'unreachable':
 				params.event = 'runner_on_unreachable';
 				break;
 			case 'ok':
 				params.event = 'runner_on_ok';
                params.changed = 'false';
 				break;
 			case 'failed':
 				params.event = 'runner_on_failed';
 				break;
 			case 'changed':
                params.event = 'runner_on_ok';
 				params.changed = true;
 				break;
 			default:
 				break;
 		}
	 	JobDetailService.getRelatedJobEvents($stateParams.id, params)
 			.success(function(res){
 				$scope.results = res.results;
 				Wait('stop');
	 		});
 	};

 	$scope.filters = ['all', 'changed', 'failed', 'ok', 'unreachable', 'skipped'];

 	// watch select2 for changes
 	$('.HostEvents-select').on("select2:select", function () {
 	 	$scope.activeFilter = $('.HostEvents-select').val();
 	 	$scope.search();
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
 			$scope.activeFilter = $stateParams.filter;
 			$scope.search();
	 		$('#HostEvents').modal('show');
 		}
 		else{
 			$scope.results = hosts.data.results;
	 		$('#HostEvents').modal('show');
 		}
 	};


 	init();

 	}];
