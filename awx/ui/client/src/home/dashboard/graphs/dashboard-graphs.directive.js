/* jshint unused: vars */
export default ['templateUrl',
    function(templateUrl) {
        return {
            restrict: 'E',
            scope: true,
            templateUrl: templateUrl('home/dashboard/graphs/dashboard-graphs'),
            link: function(scope, element, attrs) {

                function clearStatus() {
                    scope.isSuccessful = true;
                    scope.isFailed = true;
                }

                clearStatus();
                scope.jobStatusSelected = true;
                scope.$broadcast("resizeGraphs");

            }
        };
    }
];
