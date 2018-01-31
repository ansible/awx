function CapacityBar (templateUrl, strings) {
    return {
        scope: {
            capacity: '=',
            totalCapacity: '=',
            labelValue: '@',
            badge: '='
        },
        templateUrl: templateUrl('instance-groups/capacity-bar/capacity-bar'),
        restrict: 'E',
        link: function(scope) {
            scope.isOffline = false;

            scope.$watch('totalCapacity', function(val) {
                if (val === 0) {
                    scope.isOffline = true;
                    scope.labelValue = strings.get(`capacityBar.IS_OFFLINE_LABEL`);
                    scope.offlineTip = strings.get(`capacityBar.IS_OFFLINE`);
                } else {
                    scope.isOffline = false;
                    scope.offlineTip = null;
                }
            }, true);

            scope.$watch('capacity', function() {
                if (scope.totalCapacity !== 0) {
                    var percentageCapacity = Math
                        .round(scope.capacity / scope.totalCapacity * 1000) / 10;

                    scope.CapacityStyle = {
                        'flex-grow': percentageCapacity * 0.01
                    };

                    scope.consumedCapacity = `${percentageCapacity}%`;
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

CapacityBar.$inject = [
    'templateUrl',
    'InstanceGroupsStrings'
];

export default CapacityBar;