function CapacityAdjuster (templateUrl) {
    return {
        scope: {
            state: '='
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
                const data = {
                    "capacity_adjustment": `${state.capacity_adjustment}`
                };
                const req = {
                    method: 'PUT',
                    url: state.url,
                    data
                };
                $http(req);
            };
        },
        controllerAs: 'vm'
    };
}

CapacityAdjuster.$inject = [
    'templateUrl'
];

export default CapacityAdjuster;