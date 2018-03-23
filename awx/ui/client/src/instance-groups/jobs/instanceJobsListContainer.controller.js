
function InstanceGroupJobsContainerController (strings, $state) {
    const vm = this || {};

    init();
    function init() {
        const instanceGroupId = $state.params.instance_group_id;

        vm.panelTitle = 'Jobs'
        vm.strings = strings;
    }

}

InstanceGroupJobsContainerController.$inject = [
    'InstanceGroupsStrings',
    '$state'
];

export default InstanceGroupJobsContainerController;
