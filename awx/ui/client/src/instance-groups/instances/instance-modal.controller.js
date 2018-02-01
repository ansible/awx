function InstanceModalController ($scope, $state, models, strings, ProcessErrors) {
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
        const associate = vm.selectedRows
            .map(instance => ({id: instance.id}));
        const disassociate = vm.deselectedRows
            .map(instance => ({id: instance.id, disassociate: true}));

        const all = associate.concat(disassociate);
        const defers = all.map((data) => {
            const config = {
                url: `${vm.instanceGroupId}/instances/`,
                data: data
            };
            return instanceGroup.http.post(config);
        });

        Promise.all(defers)
            .then(vm.onSaveSuccess)
            .catch(({data, status}) => {
                ProcessErrors($scope, data, status, null, {
                    hdr: 'Error!',
                    msg: 'Call failed. Return status: ' + status
                });
            });
    };

    vm.onSaveSuccess = () => {
        $state.go('instanceGroups.instances', {}, {reload: 'instanceGroups.instances'});
    };
}

InstanceModalController.$inject = [
    '$scope',
    '$state',
    'resolvedModels',
    'InstanceGroupsStrings',
    'ProcessErrors'
];

export default InstanceModalController;
