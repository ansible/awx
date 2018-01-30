function InstanceModalController ($scope, $state, $http, $q, models, strings) {
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
        vm.relatedInstances = instanceGroup.get('related.instances.results');
        vm.relatedInstanceIds = vm.relatedInstances.map(instance => instance.id);
        vm.instances = instance.get('results').map(instance => {
            instance.isSelected = vm.relatedInstanceIds.includes(instance.id);
            return instance;
        });
    };

    init();

    function init() {
        vm.strings = strings;
        vm.panelTitle = strings.get('instance.PANEL_TITLE');
        vm.instanceGroupId = instanceGroup.get('id');

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
        let associate = vm.selectedRows
            .map(instance => ({id: instance.id}));
        let disassociate = vm.deselectedRows
            .map(instance => ({id: instance.id, disassociate: true}));

        let all = associate.concat(disassociate);
        let defers = all.map((data) => {
            let config = {
                url: `${vm.instanceGroupId}/instances/`,
                data: data
            };
            return instanceGroup.http.post(config);
        });

        Promise.all(defers)
            .then(vm.onSaveSuccess);
    };

    vm.onSaveSuccess = () => {
        $state.go('instanceGroups.instances', {}, {reload: 'instanceGroups.instances'});
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
