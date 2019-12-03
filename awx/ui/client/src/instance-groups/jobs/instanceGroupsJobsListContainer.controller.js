
function InstanceGroupJobsContainerController ($scope, strings, $state) {
    const vm = this || {};
    const instanceGroupId = $state.params.instance_group_id;

    let tabs = {};
    if ($state.is('instanceGroups.jobs')) {
        tabs =  {
            state: {
                details: {
                    _go: 'instanceGroups.edit'
                },
                instances: {
                    _go: 'instanceGroups.instances'
                },
                jobs: {
                    _active: true,
                    _go: 'instanceGroups.jobs'
                }
            }
        };
    } else if ($state.is('instanceGroups.containerGroupJobs')) {
        tabs =  {
            state: {
                details: {
                    _go: 'instanceGroups.editContainerGroup'
                },
                instances: {
                    _go: 'instanceGroups.containerGroupInstances'
                },
                jobs: {
                    _active: true,
                    _go: 'instanceGroups.containerGroupJobs'
                }
            }
        };
    }

    vm.panelTitle = strings.get('jobs.PANEL_TITLE');
    vm.strings = strings;
    const tabObj = {};

    tabObj.details = { _go: tabs.state.details._go, _params: { instance_group_id: parseInt(instanceGroupId) } };
    tabObj.instances = { _go: tabs.state.instances._go, _params: { instance_group_id: parseInt(instanceGroupId) } };
    tabObj.jobs = { _go: tabs.state.jobs._go, _params: { instance_group_id: parseInt(instanceGroupId) }, _active: true };
    vm.tab = tabObj;

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
