function atPanelLink (scope, el, attrs, controllers) {
    let panelController = controllers[0];

    panelController.init(scope, el);
}

function AtPanelController ($state) {
    let vm = this;

    let scope;
    let el;

    vm.init = (_scope_, _el_) => {
        scope = _scope_;
        el = _el_;
    };

    vm.dismiss = () => {
        $state.go('^');
    };

    vm.use = child => {
        child.dismiss = vm.dismiss;
    };
}

AtPanelController.$inject = ['$state'];

function atPanel (pathService, _$animate_) {
    return {
        restrict: 'E',
        replace: true,
        require: ['atPanel'],
        transclude: true,
        templateUrl: pathService.getPartialPath('components/panel/panel'),
        controller: AtPanelController,
        controllerAs: 'vm',
        link: atPanelLink,
        scope: {
            state: '=',
            animate: '@'
        }
    };
}

atPanel.$inject = ['PathService'];

export default atPanel;
