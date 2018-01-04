function NetworkingController (models, $state, $scope, strings) {
    const vm = this || {};

    const {
        inventory
    } = models;

    vm.strings = strings;
    vm.panelTitle = `${strings.get('state.BREADCRUMB_LABEL')} | ${inventory.name}`;
    vm.hostDetail = false;

    vm.panelIsExpanded = false;

    vm.togglePanel = () => {
        vm.panelIsExpanded = !vm.panelIsExpanded;
    };

    vm.close = () => {
        $state.go('inventories');
    };

    $scope.$on('closeDetailsPanel', () => {
        vm.panelIsExpanded = false;
    });

    $scope.$on('retrievedHostData', (e, hostData, expand) => {
        if (expand) {
            vm.panelIsExpanded = true;
        }
        if (_.isEmpty(hostData)) {
            $scope.hostDetail = false;
        } else {
            $scope.hostDetail = hostData;
        }
    });
}

NetworkingController.$inject = [
    'resolvedModels',
    '$state',
    '$scope',
    'NetworkingStrings'
];

export default NetworkingController;
