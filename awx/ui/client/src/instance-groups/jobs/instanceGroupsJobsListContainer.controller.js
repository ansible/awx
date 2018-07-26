
function InstanceGroupJobsContainerController ($scope, strings, $state) {
    const vm = this || {};

    const instanceGroupId = $state.params.instance_group_id;

    vm.panelTitle = strings.get('jobs.PANEL_TITLE');
    vm.strings = strings;

    vm.tab = {
        details: {
            _go: 'instanceGroups.edit',
            _params: { instance_group_id: instanceGroupId },
            _label: strings.get('tab.DETAILS')
        },
        instances: {
            _go: 'instanceGroups.instances',
            _params: { instance_group_id: instanceGroupId },
            _label: strings.get('tab.INSTANCES')
        },
        jobs: {
            _active: true,
            _params: { instance_group_id: instanceGroupId },
            _label: strings.get('tab.JOBS')
        }
    };

    $scope.$on('updateCount', (e, count) => {
        if (typeof count === 'number') {
            vm.count = count;
        }
    });
}

InstanceGroupJobsContainerController.$inject = [
    '$scope',
    'InstanceGroupsStrings',
    '$state'
];

export default InstanceGroupJobsContainerController;
