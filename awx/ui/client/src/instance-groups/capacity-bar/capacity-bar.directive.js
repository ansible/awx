export default ['templateUrl',
    function (templateUrl) {
        return {
            scope: {
                capacity: '=',
                totalCapacity: '='
            },
            templateUrl: templateUrl('instance-groups/capacity-bar/capacity-bar'),
            restrict: 'E',
            link: function(scope) {
                scope.isOffline = false;

                scope.$watch('totalCapacity', function(val) {
                    if (val === 0) {
                        scope.isOffline = true;
                    } else {
                        scope.isOffline = false;
                    }
                }, true);

                scope.$watch('capacity', function() {
                    if (scope.totalCapacity !== 0) {
                        scope.CapacityStyle = {
                            'flex-grow': scope.capacity * 0.01
                        };

                        scope.consumedCapacity = `${scope.capacity}%`;
                    } else {
                        scope.CapacityStyle = {
                            'flex-grow': 1
                        };

                        scope.consumedCapacity = null;
                    }
                }, true);
            }
        };
    }
];
