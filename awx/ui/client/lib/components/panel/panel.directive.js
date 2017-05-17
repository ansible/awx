function use (scope) {
    scope.dismiss = this.dismiss;
}

function dismiss ($state) {
    $state.go('^');
}

function AtPanelController ($state) {
    let vm = this;

    vm.dismiss = dismiss.bind(vm, $state);
    vm.use = use;
}

AtPanelController.$inject = ['$state'];

function atPanel (pathService) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl: pathService.getPartialPath('components/panel/panel'),
        controller: AtPanelController,
        controllerAs: 'vm',
        scope: {
            state: '='
        }
    };
}

atPanel.$inject = ['PathService'];

export default atPanel;
