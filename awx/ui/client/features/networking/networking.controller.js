function NetworkingController (models, $state, $scope, strings, CreateSelect2) {
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
    vm.keyPanelExpanded = false;
    vm.close = () => {
        $state.go('inventories');
    };

    vm.redirectButtonHandler = (string) => {
        $scope.$broadcast('toolbarButtonEvent', string);
    };

    vm.jumpTo = (thing) => {
        vm.jumpToPanelExpanded = !vm.jumpToPanelExpanded;
        vm.keyPanelExpanded = false;
        if (thing && typeof thing === 'string') {
            $scope.$broadcast('jumpTo', thing);
        }
        if (thing && typeof thing === 'object') {
            $scope.$broadcast('search', thing);
        }
    };

    vm.key = () => {
        vm.keyPanelExpanded = !vm.keyPanelExpanded;
        vm.jumpToPanelExpanded = false;
    };

    $scope.$on('overall_toolbox_collapsed', () => {
        vm.leftPanelIsExpanded = !vm.leftPanelIsExpanded;
    });

    $scope.$on('closeDetailsPanel', () => {
        vm.rightPanelIsExpanded = false;
        vm.jumpToPanelExpanded = false;
        vm.keyPanelExpanded = false;
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

    $scope.$on('select', (e, options) => {
        $scope.devices = options;
        CreateSelect2({
            element: '#networking-search',
            multiple: false,
            addNew: true,
            scope: $scope,
            options: 'devices',
            placeholder: 'SEARCH'
        });
    });

    $('#networking-search').on('select2:select', (e) => {
        $scope.$broadcast('search', e.params.data);
    });
}

NetworkingController.$inject = [
    'resolvedModels',
    '$state',
    '$scope',
    'NetworkingStrings',
    'CreateSelect2'
];

export default NetworkingController;
