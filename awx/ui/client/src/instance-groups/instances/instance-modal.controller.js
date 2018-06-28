function InstanceModalController ($scope, $state, models, strings, ProcessErrors, Wait) {
    const { instance, instanceGroup } = models;
    const vm = this || {};
    let relatedInstanceIds = [];

    vm.setInstances = () => {
        vm.relatedInstances = [];
        vm.selectedRows = [];
        vm.instances = instance.get('results').map(instance => {
            instance.isSelected = false;
            return instance;
        });
    };

    vm.setRelatedInstances = () => {
        vm.instanceGroupName = instanceGroup.get('name');
        vm.relatedInstances = instanceGroup.get('related.instances.results');
        vm.selectedRows = _.cloneDeep(vm.relatedInstances);
        relatedInstanceIds = vm.relatedInstances.map(instance => instance.id);
        vm.instances = instance.get('results').map(instance => {
            instance.isSelected = relatedInstanceIds.includes(instance.id);
            return instance;
        });
    };

    init();

    function init() {
        vm.strings = strings;
        vm.panelTitle = strings.get('instance.PANEL_TITLE');
        vm.instanceGroupId = instanceGroup.get('id');

        vm.dataset = instance.get();
        vm.querySet = { order_by: 'hostname', page_size: '5' };

        vm.list = {
            name: 'instances',
            iterator: 'instance',
            basePath: `/api/v2/instances/`
        };

        if (vm.instanceGroupId === undefined) {
            vm.setInstances();
        } else {
            vm.setRelatedInstances();
        }

        $scope.$watch('vm.instances', function() {
            angular.forEach(vm.instances, function(instance) {
                instance.isSelected = _.filter(vm.selectedRows, 'id', instance.id).length > 0;
            });
        });
    }

    vm.submit = () => {
        Wait('start');
        const selectedRowIds = vm.selectedRows.map(instance => instance.id);

        const associate = selectedRowIds.filter(instanceId => {
            return !relatedInstanceIds.includes(instanceId);
        }).map(id => ({id}));
        const disassociate = relatedInstanceIds.filter(instanceId => {
            return !selectedRowIds.includes(instanceId);
        }).map(id => ({id, disassociate: true}));

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
            })
            .finally(() => {
                Wait('stop');
            });
    };

    vm.onSaveSuccess = () => {
        $state.go('instanceGroups.instances', {}, {reload: 'instanceGroups.instances'});
    };

    vm.dismiss = () => {
        $state.go('instanceGroups.instances');
    };

    vm.toggleRow = (row) => {
        if (row.isSelected) {
            let matchingIndex;
            angular.forEach(vm.selectedRows, function(value, index) {
                if(row.id === vm.selectedRows[index].id) {
                    matchingIndex = index;
                }
            });

            vm.selectedRows.splice(matchingIndex, 1);
            row.isSelected = false;
        } else {
            row.isSelected = true;
            vm.selectedRows.push(row);
        }

    };
}

InstanceModalController.$inject = [
    '$scope',
    '$state',
    'resolvedModels',
    'InstanceGroupsStrings',
    'ProcessErrors',
    'Wait'
];

export default InstanceModalController;
