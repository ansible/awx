/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
 	['$scope', '$rootScope', '$stateParams', 'JobDetailService', 'jobSocket', function($scope, $rootScope, $stateParams, JobDetailService, jobSocket){

 		// the job_events socket should be substituted for a job_host_summary socket post 3.0 
        var page_size = 200;
        var socketListener = function(){
        	console.log(jobSocket)
        	jobSocket.on('summary_complete', function(data) {
        		JobDetailService.getJob($stateParams.id).success(function(res){
        			console.log('job at summary_complete.', res)
        		});
        	});
        	jobSocket.on('status_changed', function(data) {
        		JobDetailService.getJob($stateParams.id).success(function(res){
        			console.log('job at data.stats.', data.status, res)
        		});
        		JobDetailService.getJobHostSummaries($stateParams.id, {}).success(function(res){
        			console.log('jobhostSummaries at summary_complete.', data.status, res)
        		});
        	});
        }
 		$scope.loading = $scope.hosts.length > 0 ? false : true;
 		$scope.done = true;
 		$scope.events = [];
 		$scope.$watchCollection('events', function(c){
	 		var filtered = $scope.events.filter(function(event){
	 			return ((event.failed || event.changed ||
	 				'runner_on_ok' || 'runner_on_async_ok' ||
	 				'runner_on_unreachable' || 'runner_on_skipped')
	 				&& event.host_name != '');
	 		});
	 		var grouped = _.groupBy(filtered, 'host_name');
	 		//$scope.hosts =              		
 		});


 		$scope.search = function(host_name){};
 		$scope.filter = function(filter){};

    	var init = function(){
    		socketListener();
        	JobDetailService.getJobHostSummaries($stateParams.id, {}).success(function(res){
        			console.log('jobhostSummaries at init.', res)
        		});    		
        };
    	init();
 	}];