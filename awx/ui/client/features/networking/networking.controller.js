function NetworkingController (models, $state, $scope, strings) {
    const vm = this || {};

    const {
        inventory
    } = models;

    vm.strings = strings;
    vm.panelTitle = `${strings.get('state.BREADCRUMB_LABEL')} | ${inventory.name}`;

    vm.panelIsExpanded = false;

    vm.togglePanel = () => {
        vm.panelIsExpanded = !vm.panelIsExpanded;
    };

    vm.close = () => {
        $state.go('inventories');
    };
}

NetworkingController.$inject = [
    'resolvedModels',
    '$state',
    '$scope',
    'NetworkingStrings'
];

export default NetworkingController;
