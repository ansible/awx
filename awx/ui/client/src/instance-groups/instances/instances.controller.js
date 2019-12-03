function InstancesController ($scope, $state, $http, $transitions, models, strings, Dataset, ProcessErrors) {
    const { instanceGroup } = models;
    const vm = this || {};
    let paginateQuerySet = {};
    vm.strings = strings;
    vm.panelTitle = instanceGroup.get('name');
    vm.instance_group_id = instanceGroup.get('id');
    vm.policy_instance_list = instanceGroup.get('policy_instance_list');
    vm.isSuperuser = $scope.$root.user_is_superuser;

    let tabs = {};
    let addInstancesRoute ="";
    if ($state.is("instanceGroups.instances")) {
        tabs={ state: {
                    details: {
                        _go: 'instanceGroups.edit'
                    },
                    instances: {
                        _active: true,
                        _go: 'instanceGroups.instances'
                    },
                    jobs: {
                        _go: 'instanceGroups.jobs'
                    }
                }
            };
        addInstancesRoute = 'instanceGroups.instances.modal.add';
    } else if ($state.is("instanceGroups.containerGroupInstances")) {
        tabs={
            state: {
                details: {
                    _go: 'instanceGroups.editContainerGroup'
                },
                instances: {
                    _active: true,
                    _go: 'instanceGroups.containerGroupInstances'
                },
                jobs: {
                    _go: 'instanceGroups.containerGroupJobs'
                }
            }
        };
        addInstancesRoute = 'instanceGroups.containerGroupInstances.modal.add';
    }

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

    vm.addInstances = () => {

        return $state.go(`${addInstancesRoute}`);
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

    const tabObj = {};
    const params = { instance_group_id: instanceGroup.get('id') };

    tabObj.details = { _go: tabs.state.details._go, _params: params };
    tabObj.instances = { _go: tabs.state.instances._go, _params: params, _active: true };
    tabObj.jobs = { _go: tabs.state.jobs._go, _params: params };
    vm.tab = tabObj;


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
    'ProcessErrors',
];

export default InstancesController;
