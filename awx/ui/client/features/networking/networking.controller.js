function NetworkingController (models, $state, $scope, strings) {
    const vm = this || {};

    const {
        inventory
    } = models;

    vm.strings = strings;
    vm.panelTitle = `${strings.get('state.BREADCRUMB_LABEL')} | ${inventory.name}`;
    vm.hostDetail = {};

    vm.rightPanelIsExpanded = false;
    vm.leftPanelIsExpanded = true;
    vm.jumpToPanelExpanded = false;
    vm.close = () => {
        $state.go('inventories');
    };

    vm.redirectButtonHandler = (string) => {
        $scope.$broadcast('toolbarButtonEvent', string);
    };

    vm.jumpTo = (string) => {
        vm.jumpToPanelExpanded = !vm.jumpToPanelExpanded;
        if (string) {
            $scope.$broadcast('jumpTo', string);
        }
    };

    $scope.$on('overall_toolbox_collapsed', () => {
        vm.leftPanelIsExpanded = !vm.leftPanelIsExpanded;
    });

    $scope.$on('closeDetailsPanel', () => {
        vm.rightPanelIsExpanded = false;
    });

    $scope.$on('showDetails', (e, data, expand) => {
        if (expand) {
            vm.rightPanelIsExpanded = true;
        }
        if (!_.has(data, 'host_id')) {
            $scope.item = data;
        } else {
            $scope.item = data;
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
