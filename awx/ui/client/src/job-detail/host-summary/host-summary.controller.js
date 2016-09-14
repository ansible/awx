/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$scope', '$rootScope', '$stateParams', 'Wait', 'JobDetailService', 'DrawGraph', function($scope, $rootScope, $stateParams, Wait, JobDetailService, DrawGraph){

        var page_size = 200;
        $scope.loading = $scope.hosts.length > 0 ? false : true;
        $scope.filter = 'all';

        var buildGraph = function(hosts){
            //  status waterfall: unreachable > failed > changed > ok > skipped
            var count;
            count = {
                ok : _.filter(hosts, function(o){
                    return o.failures === 0 && o.changed === 0 && o.ok > 0;
                }),
                skipped : _.filter(hosts, function(o){
                    return o.skipped > 0;
                }),
                unreachable : _.filter(hosts, function(o){
                    return o.dark > 0;
                }),
                failures : _.filter(hosts, function(o){
                    return o.failed === true;
                }),
                changed : _.filter(hosts, function(o){
                    return o.changed > 0;
                })
            };
            return count;
        };
        var init = function(){
            Wait('start');
            JobDetailService.getJobHostSummaries($stateParams.id, {page_size: page_size, order_by: 'host_name'})
            .success(function(res){
                $scope.hosts = res.results;
                $scope.next = res.next;
                $scope.count = buildGraph(res.results);
                Wait('stop');
                DrawGraph({count: $scope.count, resize:true});
            });
            JobDetailService.getJob({id: $stateParams.id})
            .success(function(res){
                $scope.status = res.results[0].status;
            });
        };
        if ($rootScope.removeJobStatusChange) {
            $rootScope.removeJobStatusChange();
        }
        // emitted by the API in the same function used to persist host summary data
        // JobEvent.update_host_summary_from_stats() from /awx/main.models.jobs.py
        $rootScope.removeJobStatusChange = $rootScope.$on('ws-JobSummaryComplete', function(e, data) {
            // discard socket msgs we don't care about in this context
            if (parseInt($stateParams.id) === data.unified_job_id){
                init();
            }
        });

        if ($rootScope.removeJobSummaryComplete) {
            $rootScope.removeJobSummaryComplete();
        }
        $rootScope.removeJobSummaryComplete = $rootScope.$on('ws-jobDetail-jobs', function(e, data) {
            if (parseInt($stateParams.id) === data.unified_job_id){
                $scope.status = data.status;
            }
        });


        $scope.buildTooltip = function(n, status){
            var grammar = function(n, status){
                var dict = {
                    0: 'No host events were ',
                    1: ' host event was ',
                    2: ' host events were '
                };
                if (n >= 2){
                    return n + dict[2] + status;
                }
                else{
                    return n !== 0 ? n + dict[n] + status : dict[n] + status;
                }
            };
            return grammar(n, status);
        };
        $scope.getNextPage = function(){
            if ($scope.next){
                JobDetailService.getNextPage($scope.next).success(function(res){
                    res.results.forEach(function(key, index){
                        $scope.hosts.push(res.results[index]);
                    });
                    $scope.hosts.push(res.results);
                    $scope.next = res.next;
                });
            }
        };
        $scope.search = function(){
            if($scope.searchTerm && $scope.searchTerm !== '') {
                $scope.searchActive = true;
                Wait('start');
                JobDetailService.getJobHostSummaries($stateParams.id, {
                    page_size: page_size,
                    host_name__icontains: encodeURIComponent($scope.searchTerm),
                }).success(function(res){
                    $scope.hosts = res.results;
                    $scope.next = res.next;
                    Wait('stop');
                });
            }
        };
        $scope.clearSearch = function(){
            $scope.searchActive = false;
            $scope.searchTerm = null;
            init();
        };
        $scope.setFilter = function(filter){
            $scope.filter = filter;
            var getAll = function(){
                Wait('start');
                JobDetailService.getJobHostSummaries($stateParams.id, {
                    page_size: page_size,
                    order_by: 'host_name'
                }).success(function(res){
                    Wait('stop');
                    $scope.hosts = res.results;
                    $scope.next = res.next;
                });
            };
            var getFailed = function(){
                Wait('start');
                JobDetailService.getJobHostSummaries($stateParams.id, {
                    page_size: page_size,
                    failed: true,
                    order_by: 'host_name'
                }).success(function(res){
                    Wait('stop');
                    $scope.hosts = res.results;
                    $scope.next = res.next;
                });
            };
            $scope.get = filter === 'all' ? getAll() : getFailed();
        };

        init();
        // calling the init routine twice will size the d3 chart correctly - no idea why
        // instantiating the graph inside a setTimeout() SHOULD have the same effect, but it doesn't
        // instantiating the graph further down the promise chain e.g. .then() or .finally() also does not work
        init();
    }];
