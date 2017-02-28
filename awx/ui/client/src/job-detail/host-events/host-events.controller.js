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

 	$scope.filters = ['all', 'changed', 'failed', 'ok', 'unreachable', 'skipped'];

 	// watch select2 for changes
 	$('.HostEvents-select').on("select2:select", function () {
 	 	  $scope.activeFilter = $('.HostEvents-select').val();
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

	 		$('#HostEvents').modal('show');
 		}
 		else{
 			$scope.results = hosts.data.results;
	 		$('#HostEvents').modal('show');
 		}
 	};


 	init();

 	}];
