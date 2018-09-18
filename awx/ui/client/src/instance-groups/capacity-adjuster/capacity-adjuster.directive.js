function CapacityAdjuster (templateUrl, ProcessErrors, Wait, strings) {
    return {
        scope: {
            state: '=',
            disabled: '@'
        },
        templateUrl: templateUrl('instance-groups/capacity-adjuster/capacity-adjuster'),
        restrict: 'E',
        replace: true,
        link: function(scope, el, attrs, controller) {
            const capacityAdjusterController = controller;
            const adjustment_values = [{
                label: strings.get('capacityAdjuster.CPU'),
                value: scope.state.cpu_capacity,
            },{
                label: strings.get('capacityAdjuster.RAM'),
                value: scope.state.mem_capacity
            }];

            scope.min_capacity = _.minBy(adjustment_values, 'value');
            scope.max_capacity = _.maxBy(adjustment_values, 'value');

            capacityAdjusterController.init();
        },
        controller: ['$scope', '$http', 'InstanceGroupsStrings',
            function($scope, $http, strings) {
                const vm = this || {};
                vm.strings = strings;

                function computeForks () {
                    $scope.forks = Math.floor($scope.min_capacity.value + ($scope.max_capacity.value - $scope.min_capacity.value) * $scope.state.capacity_adjustment);
                }

                vm.init = () => {
                    computeForks();
                };

                vm.slide = (state) => {
                    Wait('start');

                    computeForks();

                    const data = {
                        "capacity_adjustment": `${state.capacity_adjustment}`
                    };
                    const req = {
                        method: 'PUT',
                        url: state.url,
                        data
                    };
                    $http(req)
                        .catch(({data, status}) => {
                            ProcessErrors(data, status, null, {
                                hdr: 'Error!',
                                msg: 'Call failed. Return status: ' + status
                            });
                        })
                        .finally(() => {
                            Wait('stop');
                        });
                };
            }
        ],
        controllerAs: 'vm'
    };
}

CapacityAdjuster.$inject = [
    'templateUrl',
    'ProcessErrors',
    'Wait',
    'InstanceGroupsStrings'
];

export default CapacityAdjuster;
