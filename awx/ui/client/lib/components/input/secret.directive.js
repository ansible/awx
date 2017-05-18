function atInputSecretLink (scope, el, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    if (scope.tab === '1') {
        el.find('input')[0].focus();
    }

    inputController.init(scope, formController);
}

function AtInputSecretController (baseInputController) {
    let vm = this || {};

    vm.init = (scope, form) => {
        baseInputController.call(vm, 'input', scope, form);

        vm.check();
    };
}

AtInputSecretController.$inject = ['BaseInputController'];

function atInputSecret (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputSecret'],
        templateUrl: pathService.getPartialPath('components/input/secret'),
        controller: AtInputSecretController,
        controllerAs: 'vm',
        link: atInputSecretLink,
        scope: {
            state: '=',
            col: '@',
            tab: '@'
        }
    };
}

atInputSecret.$inject = ['PathService'];

export default atInputSecret;
