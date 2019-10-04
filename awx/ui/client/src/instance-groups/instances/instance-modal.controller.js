function InstanceModalController ($scope, $state, Dataset, models, strings, ProcessErrors, Wait, routeData) {
    const { instanceGroup } = models;
    const vm = this || {};
    let relatedInstanceIds = [];
    let paginateQuerySet = {};

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

        vm.list = {
            name: 'instances',
            iterator: 'add_instance',
            basePath: `/api/v2/instances/`
        };

        vm.instances = Dataset.data.results;
        vm.instance_dataset = Dataset.data;

        setRelatedInstances();
    }

    const toolbarSortDefault = {
      label: `${strings.get('sort.NAME_ASCENDING')}`,
      value: 'hostname'
    };

    vm.toolbarSortValue = toolbarSortDefault;
    vm.toolbarSortOptions = [
        toolbarSortDefault,
        { label: `${strings.get('sort.NAME_DESCENDING')}`, value: '-hostname' },
        { label: `${strings.get('sort.UUID_ASCENDING')}`, value: 'uuid' },
        { label: `${strings.get('sort.UUID_DESCENDING')}`, value: '-uuid' },
        { label: `${strings.get('sort.CREATED_ASCENDING')}`, value: 'created' },
        { label: `${strings.get('sort.CREATED_DESCENDING')}`, value: '-created' },
        { label: `${strings.get('sort.MODIFIED_ASCENDING')}`, value: 'modified' },
        { label: `${strings.get('sort.MODIFIED_DESCENDING')}`, value: '-modified' },
        { label: `${strings.get('sort.CAPACITY_ASCENDING')}`, value: 'capacity' },
        { label: `${strings.get('sort.CAPACITY_DESCENDING')}`, value: '-capacity' }
    ];

    const removeStateParamsListener = $scope.$watchCollection('$state.params', () => {
        setToolbarSort();
    });

    function setToolbarSort () {
        const orderByValue = _.get($state.params, 'add_instance_search.order_by');
        const sortValue = _.find(vm.toolbarSortOptions, (option) => option.value === orderByValue);
        if (sortValue) {
            vm.toolbarSortValue = sortValue;
        } else {
            vm.toolbarSortValue = toolbarSortDefault;
        }
    }

    vm.onToolbarSort = (sort) => {
        vm.toolbarSortValue = sort;

        const queryParams = Object.assign(
            {},
            $state.params.add_instance_search,
            paginateQuerySet,
            { order_by: sort.value }
        );

        $state.go('.', {
            add_instance_search: queryParams
        }, { notify: false, location: 'replace' });
    };

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
        $state.go(`${routeData}`, {}, {reload: `${routeData}`});
    };

    vm.dismiss = () => {
        $state.go(`${routeData}`);
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

    const removeUpdateDatasetListener = $scope.$on('updateDataset', (e, dataset, queryset) => {
        vm.instances = dataset.results;
        vm.instance_dataset = dataset;
        paginateQuerySet = queryset;

        angular.forEach(vm.instances, function(instance) {
            instance.isSelected = _.filter(vm.selectedRows, { 'id': instance.id }).length > 0;
        });
    });

    $scope.$on('$destroy', function() {
        removeUpdateDatasetListener();
        removeStateParamsListener();
    });
}

InstanceModalController.$inject = [
    '$scope',
    '$state',
    'Dataset',
    'resolvedModels',
    'InstanceGroupsStrings',
    'ProcessErrors',
    'Wait',
    'routeData'
];

export default InstanceModalController;
