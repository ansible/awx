
function InstanceGroupJobsContainerController ($scope, strings) {
    const vm = this || {};

    init();
    function init() {
        vm.panelTitle = strings.get('jobs.PANEL_TITLE');
        vm.strings = strings;
    }

    $scope.$on('updateCount', (e, count) => {
        if (typeof count === 'number') {
            vm.count = count;
        }
    });
}

InstanceGroupJobsContainerController.$inject = [
    '$scope',
    'InstanceGroupsStrings'
];

export default InstanceGroupJobsContainerController;
