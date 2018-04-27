function CapacityAdjuster (templateUrl, ProcessErrors, Wait) {
    return {
        scope: {
            state: '=',
            disabled: '@'
        },
        templateUrl: templateUrl('instance-groups/capacity-adjuster/capacity-adjuster'),
        restrict: 'E',
        replace: true,
        link: function(scope) {
            const adjustment_values = [{
                label: 'CPU',
                value: scope.state.cpu_capacity,
            },{
                label: 'RAM',
                value: scope.state.mem_capacity
            }];

            scope.min_capacity = _.min(adjustment_values, 'value');
            scope.max_capacity = _.max(adjustment_values, 'value');
        },
        controller: function($http) {
            const vm = this || {};

            vm.slide = (state) => {
                Wait('start');
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
        },
        controllerAs: 'vm'
    };
}

CapacityAdjuster.$inject = [
    'templateUrl',
    'ProcessErrors',
    'Wait'
];

export default CapacityAdjuster;