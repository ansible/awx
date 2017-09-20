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
                    scope.CapacityStyle = {
                        'flex-grow': scope.capacity * 0.01
                    };
                }, true);
            }
        };
    }
];
