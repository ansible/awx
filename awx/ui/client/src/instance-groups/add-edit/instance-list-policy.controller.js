function InstanceModalController ($scope, $state, models, strings) {
    const { instance, instanceGroup } = models;
    const vm = this || {};

    vm.setInstances = () => {
        vm.instances = instance.get('results').map(instance => {
            instance.isSelected = false;
            return instance;
        });
    };

    vm.setRelatedInstances = () => {
        vm.instanceGroupName = instanceGroup.get('name');
        vm.relatedInstances = instanceGroup.get('policy_instance_list');

        vm.instances = instance.get('results').map(instance => {
            instance.isSelected = vm.relatedInstances.includes(instance.hostname);
            return instance;
        });
    };

    init();

    function init() {
        vm.strings = strings;
        vm.instanceGroupId = instanceGroup.get('id');
        vm.defaultParams = { page_size: '10', order_by: 'hostname' };

        if (vm.instanceGroupId === undefined) {
            vm.setInstances();
        } else {
            vm.setRelatedInstances();
        }
    }

    $scope.$watch('vm.instances', function() {
        vm.selectedRows = _.filter(vm.instances, 'isSelected');
        vm.deselectedRows = _.filter(vm.instances, 'isSelected', false);
     }, true);

    vm.submit = () => {
        $scope.$parent.$parent.$parent.state.policy_instance_list._value = vm.selectedRows;
        $state.go("^.^");
    };
}

InstanceModalController.$inject = [
    '$scope',
    '$state',
    'resolvedModels',
    'InstanceGroupsStrings'
];

export default InstanceModalController;
