function IndexTemplatesController ($scope, $state, strings) {
    const vm = this;
    vm.strings = strings;

    $scope.filterUser = () => {
        $state.go('portalMode.myJobs');
    };
    $scope.filterAll = () => {
        $state.go('portalMode.allJobs');
    };

    $scope.$on('updateCount', (e, count, resource) => {
        if (resource === 'jobs') {
            vm.jobsCount = count;
        } else if (resource === 'templates') {
            vm.templatesCount = count;
        }
    });
}

IndexTemplatesController.$inject = [
    '$scope',
    '$state',
    'PortalModeStrings',
];

export default IndexTemplatesController;
