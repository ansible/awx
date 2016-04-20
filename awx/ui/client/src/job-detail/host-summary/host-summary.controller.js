/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$scope', '$rootScope', '$stateParams', 'Wait', 'JobDetailService', 'jobSocket', 'DrawGraph', function($scope, $rootScope, $stateParams, Wait, JobDetailService, jobSocket, DrawGraph){

        var page_size = 200;
        $scope.loading = $scope.hosts.length > 0 ? false : true;
        $scope.filter = 'all';
        $scope.search = null;

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
        var socketListener = function(){
            // emitted by the API in the same function used to persist host summary data
            // JobEvent.update_host_summary_from_stats() from /awx/main.models.jobs.py 
            jobSocket.on('summary_complete', function(data) {
                // discard socket msgs we don't care about in this context
                if ($stateParams.id == data['unified_job_id']){
                    init();
                }
            });
            // UnifiedJob.def socketio_emit_status() from /awx/main.models.unified_jobs.py 
            jobSocket.on('status_changed', function(data) {
                if ($stateParams.id == data['unified_job_id']){
                    $scope.status = data['status'];
                }
            });
        };
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
            /*
            _.forIn(count, function(value, key){
                text[key] = grammar(value.length, key);
            });
            */
            return grammar(n, status)
        };
        $scope.getNextPage = function(){
            if ($scope.next){
                JobDetailService.getNextPage($scope.next).success(function(res){
                    res.results.forEach(function(key, index){
                        $scope.hosts.push(res.results[index]);  
                    })
                    $scope.hosts.push(res.results);
                    $scope.next = res.next;
                });
            }
        };
        $scope.search = function(){
            Wait('start');
            JobDetailService.getJobHostSummaries($stateParams.id, {
                page_size: page_size,
                host_name__icontains: $scope.searchTerm,
            }).success(function(res){
                $scope.hosts = res.results;
                $scope.next = res.next;
                Wait('stop');
            })
        };
        $scope.setFilter = function(filter){
            $scope.filter = filter;
            var getAll = function(){
                Wait('start');
                JobDetailService.getJobHostSummaries($stateParams.id, {
                    page_size: page_size
                }).success(function(res){
                    Wait('stop')           
                    $scope.hosts = res.results;
                    $scope.next = res.next;
                });
            };
            var getFailed = function(){
                Wait('start');
                JobDetailService.getJobHostSummaries($stateParams.id, {
                    page_size: page_size,
                    failed: true
                }).success(function(res){
                    Wait('stop')
                    $scope.hosts = res.results;
                    $scope.next = res.next;
                });                
            }
            var get = filter == 'all' ? getAll() : getFailed();
        };

        $scope.$watchCollection('hosts', function(curr, prev){
            $scope.count = buildGraph(curr);
            DrawGraph({count: $scope.count, resize:true});
        });

        var init = function(){
            Wait('start');
            JobDetailService.getJobHostSummaries($stateParams.id, {page_size: page_size})
            .success(function(res){
                $scope.hosts = res.results;
                $scope.next = res.next;
                Wait('stop');
            });
            JobDetailService.getJob({id: $stateParams.id})
            .success(function(res){
                $scope.status = res.results[0].status;
            });
        };
        socketListener();
        init();
    }];