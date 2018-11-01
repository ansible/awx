function InstancesController ($scope, $state, $http, models, strings, Dataset, ProcessErrors) {
    const { instanceGroup } = models;
    const vm = this || {};
    vm.strings = strings;
    vm.panelTitle = instanceGroup.get('name');
    vm.instance_group_id = instanceGroup.get('id');
    vm.policy_instance_list = instanceGroup.get('policy_instance_list');
    vm.isSuperuser = $scope.$root.user_is_superuser;


    init();

    function init() {
        vm.list = {
            name: 'instances',
            iterator: 'instance',
            basePath: `/api/v2/instance_groups/${vm.instance_group_id}/instances/`
        };

        vm.dataset = Dataset.data;
        vm.instances = instanceGroup.get('related.instances.results');
    }

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
}

InstancesController.$inject = [
    '$scope',
    '$state',
    '$http',
    'resolvedModels',
    'InstanceGroupsStrings',
    'Dataset',
    'ProcessErrors'
];

export default InstancesController;
