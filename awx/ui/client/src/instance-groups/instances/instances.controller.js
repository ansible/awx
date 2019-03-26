function InstancesController ($scope, $state, $http, $transitions, models, strings, Dataset, ProcessErrors) {
    const { instanceGroup } = models;
    const vm = this || {};
    let paginateQuerySet = {};
    vm.strings = strings;
    vm.panelTitle = instanceGroup.get('name');
    vm.instance_group_id = instanceGroup.get('id');
    vm.policy_instance_list = instanceGroup.get('policy_instance_list');
    vm.isSuperuser = $scope.$root.user_is_superuser;

    vm.list = {
        name: 'instances',
        iterator: 'instance',
        basePath: `/api/v2/instance_groups/${vm.instance_group_id}/instances/`
    };
    vm.instance_dataset = Dataset.data;
    vm.instances = Dataset.data.results;

    const toolbarSortDefault = {
        label: `${strings.get('sort.NAME_ASCENDING')}`,
        value: 'hostname'
    };

    vm.toolbarSortValue = toolbarSortDefault;
    vm.toolbarSortOptions = [
        toolbarSortDefault,
        {
            label: `${strings.get('sort.NAME_DESCENDING')}`,
            value: '-hostname'
        }
    ];

    const removeStateParamsListener = $scope.$watchCollection('$state.params', () => {
        setToolbarSort();
    });

    function setToolbarSort () {
        const orderByValue = _.get($state.params, 'instance_search.order_by');
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
            $state.params.instance_search,
            paginateQuerySet,
            { order_by: sort.value }
        );

        $state.go('.', {
            instance_search: queryParams
        }, { notify: false, location: 'replace' });
    };

    vm.tab = {
        details: {
            _go: 'instanceGroups.edit',
            _params: { instance_group_id: vm.instance_group_id }
        },
        instances: {
            _active: true,
            _go: 'instanceGroups.instances',
            _params: { instance_group_id: vm.instance_group_id }
        },
        jobs: {
            _go: 'instanceGroups.jobs',
            _params: { instance_group_id: vm.instance_group_id }
        }
    };

    vm.tooltips = {
        add: strings.get('tooltips.ASSOCIATE_INSTANCES')
    };

    vm.rowAction = {
        toggle: {
            _disabled: !vm.isSuperuser
        },
        capacity_adjustment: {
            _disabled: !vm.isSuperuser
        }
    };

    vm.toggle = (toggled) => {
        const instance = _.find(vm.instances, ['id', toggled.id]);
        instance.enabled = !instance.enabled;

        const data = {
            "capacity_adjustment": instance.capacity_adjustment,
            "enabled": instance.enabled
        };

        const req = {
            method: 'PUT',
            url: instance.url,
            data
        };

        $http(req).then(vm.onSaveSuccess)
            .catch(({data, status}) => {
                ProcessErrors($scope, data, status, null, {
                    hdr: 'Error!',
                    msg: 'Call failed. Return status: ' + status
                });
            });
    };

    vm.onSaveSuccess = () => {
        $state.transitionTo($state.current, $state.params, {
            reload: true, location: true, inherit: false, notify: true
        });
    };

    $scope.isActive = function(id) {
        let selected = parseInt($state.params.instance_id);
        return id === selected;
    };

    const removeUpdateDatasetListener = $scope.$on('updateDataset', (e, dataset, queryset) => {
        vm.instances = dataset.results;
        vm.instance_dataset = dataset;
        paginateQuerySet = queryset;
    });

    const removeStateChangeListener = $transitions.onSuccess({}, function(trans) {
        if (trans.to().name === 'instanceGroups.instances.modal.add') {
            removeUpdateDatasetListener();
            removeStateChangeListener();
            removeStateParamsListener();
        }
    });

    $scope.$on('$destroy', function() {
        removeUpdateDatasetListener();
        removeStateChangeListener();
        removeStateParamsListener();
    });
}

InstancesController.$inject = [
    '$scope',
    '$state',
    '$http',
    '$transitions',
    'resolvedModels',
    'InstanceGroupsStrings',
    'Dataset',
    'ProcessErrors'
];

export default InstancesController;
