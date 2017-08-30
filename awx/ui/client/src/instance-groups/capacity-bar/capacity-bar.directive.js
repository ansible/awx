export default ['templateUrl',
    function (templateUrl) {
        return {
            scope: {
                capacity: '='
            },
            templateUrl: templateUrl('instance-groups/capacity-bar/capacity-bar'),
            restrict: 'E',
            link: function(scope) {
                scope.$watch('capacity', function() {
                    scope.CapacityStyle = {
                        'flex-grow': scope.capacity * 0.01
                    };
                }, true);
            }
        };
    }
];
