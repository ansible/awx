function use (scope) {
    scope.dismiss = this.dismiss;
}

function dismiss ($state) {
    $state.go('^');
}

function controller ($state) {
    let vm = this;

    vm.dismiss = dismiss.bind(vm, $state);
    vm.use = use;
}

controller.$inject = ['$state'];

function atPanel (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl: pathService.getPartialPath('components/panel/panel'),
        controller,
        controllerAs: 'vm',
        scope: {
            config: '='
        }
    };
}

atPanel.$inject = ['PathService'];

export default atPanel;
