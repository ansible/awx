
function InstanceGroupJobsContainerController (strings, $state) {
    const vm = this || {};

    init();
    function init() {
        const instanceGroupId = $state.params.instance_group_id;

        vm.panelTitle = 'Jobs'

        vm.tab = {
            details: {
                _go: 'instanceGroups.edit',
                _params: { instanceGroupId },
                _label: strings.get('tab.DETAILS')
            },
            instances: {
                _go: 'instanceGroups.instances',
                _params: { instanceGroupId },
                _label: strings.get('tab.INSTANCES')
            },
            jobs: {
                _active: true,
                _label: strings.get('tab.JOBS')
            }
        };
    }

}

InstanceGroupJobsContainerController.$inject = [
    'InstanceGroupsStrings',
    '$state'
];

export default InstanceGroupJobsContainerController;
