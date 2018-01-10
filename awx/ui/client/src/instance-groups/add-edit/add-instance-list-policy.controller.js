function InstanceModalController ($scope, $state, $http, $q, models, strings) {
    const { instance } = models;
    const vm = this || {};

    vm.setInstances = () => {
        vm.instances = instance.get('results').map(instance => {
            instance.isSelected = false;
            return instance;
        });
    }

    init();

    function init() {
        vm.strings = strings;
        vm.panelTitle = strings.get('instance.PANEL_TITLE');
        vm.setInstances();
    };

    $scope.$watch('vm.instances', function() {
        vm.selectedRows = _.filter(vm.instances, 'isSelected')
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
    '$http',
    '$q',
    'resolvedModels',
    'InstanceGroupsStrings'
];

export default InstanceModalController;
