
function InstanceGroupJobsContainerController (strings) {
    const vm = this || {};

    init();
    function init() {
        vm.panelTitle = strings.get('jobs.PANEL_TITLE');
        vm.strings = strings;
    }

}

InstanceGroupJobsContainerController.$inject = [
    'InstanceGroupsStrings'
];

export default InstanceGroupJobsContainerController;
