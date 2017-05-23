function AtPanelController ($state) {
    let vm = this;

    vm.dismiss = () => {
        $state.go('^');
    };

    vm.use = scope => {
        scope.dismiss = this.dismiss;
    };
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
