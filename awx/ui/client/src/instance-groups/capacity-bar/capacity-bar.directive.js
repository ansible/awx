export default ['templateUrl', 'ComponentsStrings',
    function (templateUrl, strings) {
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
                        scope.offlineTip = strings.get(`capacityBar.IS_OFFLINE`);
                    } else {
                        scope.isOffline = false;
                        scope.offlineTip = null;
                    }
                }, true);

                scope.$watch('capacity', function() {
                    if (scope.totalCapacity !== 0) {
                        scope.CapacityStyle = {
                            'flex-grow': scope.capacity / scope.totalCapacity * 0.01
                        };

                        scope.consumedCapacity = `${Math.round(scope.capacity / scope.totalCapacity * 10) / 10}%`;
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
