/* eslint-disable */
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
    $scope.devices = [];
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

    $scope.$on('instatiateSelect', (e, devices) => {
        for(var i = 0; i < devices.length; i++){
            let device = devices[i];
            $scope.devices.push({
                    value: device.id,
                    text: device.name,
                    label: device.name,
                    id: device.id
                });
        }

        $("#networking-search").select2({
            width:'100%',
            containerCssClass: 'Form-dropDown',
            placeholder: 'SEARCH'
        });
    });

    $scope.$on('addSearchOption', (e, device) => {
        $scope.devices.push({
                value: device.id,
                text: device.name,
                label: device.name,
                id: device.id
            });
    });

    $scope.$on('editSearchOption', (e, device) => {
        for(var i = 0; i < $scope.devices.length; i++){
            if(device.id === $scope.devices[i].id){
                $scope.devices[i].text = device.name;
                $scope.devices[i].label = device.name;
            }
        }
    });

    $scope.$on('removeSearchOption', (e, device) => {
        for (var i = 0; i < $scope.devices.length; i++) {
            if ($scope.devices[i].id === device.id) {
                $scope.devices.splice(i, 1);
            }
        }
    });

    $('#networking-search').on('select2:select', (e) => {
        $scope.$broadcast('search', e.params.data);
    });

    $('#networking-search').on('select2:open', () => {
        $('.select2-dropdown').addClass('Networking-dropDown');
        $scope.$broadcast('SearchDropdown');
    });

    $('#networking-search').on('select2:close', () => {
        setTimeout(function() {
            $('.select2-container-active').removeClass('select2-container-active');
            $(':focus').blur();
        }, 1);
        $scope.$broadcast('SearchDropdownClose');
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
/* eslint-disable */
