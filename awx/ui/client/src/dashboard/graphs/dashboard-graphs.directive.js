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

                    scope.toggleGraphStatus = function (graphType) {
                        clearGraphs();
                        if (graphType === "jobStatus") {
                            scope.jobStatusSelected = true;
                        } else if (graphType === "hostStatus") {
                            scope.hostStatusSelected = true;
                        }
                        scope.$broadcast("resizeGraphs");
                    };

                    // initially toggle jobStatus graph
                    clearGraphs();
                    scope.toggleGraphStatus("jobStatus");
                }
            };
        }
    ];
