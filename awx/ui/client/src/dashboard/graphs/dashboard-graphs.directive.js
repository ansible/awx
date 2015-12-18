/* jshint unused: vars */
export default
    [   'templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                scope: true,
                templateUrl: templateUrl('dashboard/graphs/dashboard-graphs'),
                link: function(scope, element, attrs) {
                    function clearGraphs() {
                        scope.jobStatusSelected = false;
                        scope.hostStatusSelected = false;
                    }

                    function clearStatus() {
                        scope.isSuccessful = true;
                        scope.isFailed = true;
                    }

                    scope.toggleGraphStatus = function (graphType) {
                        clearGraphs();
                        if (graphType === "jobStatus") {
                            scope.jobStatusSelected = true;
                        } else if (graphType === "hostStatus") {
                            scope.hostStatusSelected = true;
                        }
                        scope.$broadcast("resizeGraphs");
                    };

                    scope.toggleJobStatusGraph = function (status) {
                        if (status === "successful") {
                            scope.isSuccessful = !scope.isSuccessful;
                            if(!scope.isSuccessful && scope.isFailed){
                                status = 'successful';  
                            }
                            else if(scope.isSuccessful && scope.isFailed){
                                status = 'both';
                            }
                            else if(!scope.isSuccessful && !scope.isFailed){
                                status = 'successful';
                                scope.isFailed = true;
                            }
                        } else if (status === "failed") {
                            scope.isFailed = !scope.isFailed;
                            if(scope.isSuccessful && scope.isFailed){
                                status = 'both';
                            }
                            if(scope.isSuccessful && !scope.isFailed){
                                status = 'failed';
                            }
                            else if(!scope.isSuccessful && !scope.isFailed){
                                status = 'failed';
                                scope.isSuccessful = true;
                            }

                        }
                        scope.$broadcast("jobStatusChange", status);
                    };

                    // initially toggle jobStatus graph
                    clearStatus();
                    clearGraphs();
                    scope.toggleGraphStatus("jobStatus");
                }
            };
        }
    ];
