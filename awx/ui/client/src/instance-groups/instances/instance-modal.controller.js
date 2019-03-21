function InstanceModalController ($scope, $state, Dataset, models, strings, ProcessErrors, Wait) {
    const { instanceGroup } = models;
    const vm = this || {};
    let relatedInstanceIds = [];

    function setRelatedInstances () {
        vm.relatedInstances = instanceGroup.get('related.instances.results');
        vm.selectedRows = _.cloneDeep(vm.relatedInstances);
        relatedInstanceIds = vm.relatedInstances.map(instance => instance.id);
        vm.instances = vm.instances.map(instance => {
            instance.isSelected = relatedInstanceIds.includes(instance.id);
            return instance;
        });
    }

    init();

    function init() {
        vm.strings = strings;
        vm.panelTitle = strings.get('instance.PANEL_TITLE');
        vm.instanceGroupId = instanceGroup.get('id');
        vm.instanceGroupName = instanceGroup.get('name');

        vm.querySet = $state.params.instance_search;

        vm.list = {
            name: 'instances',
            iterator: 'instance',
            basePath: `/api/v2/instances/`
        };

        vm.instances = Dataset.data.results;
        vm.instance_dataset = Dataset.data;

        setRelatedInstances();

        $scope.$watch('vm.instances', function() {
            angular.forEach(vm.instances, function(instance) {
                instance.isSelected = _.filter(vm.selectedRows, { 'id': instance.id }).length > 0;
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
    'Dataset',
    'resolvedModels',
    'InstanceGroupsStrings',
    'ProcessErrors',
    'Wait'
];

export default InstanceModalController;
