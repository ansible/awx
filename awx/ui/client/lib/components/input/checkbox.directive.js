function atInputCheckboxLink (scope, element, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputCheckboxController (baseInputController) {
    let vm = this || {};

    vm.init = (scope, element, form) => {
        baseInputController.call(vm, 'input', scope, element, form);
        scope.label = scope.state.label;
        scope.state.label = 'OPTIONS';

        vm.check();
    };
}

AtInputCheckboxController.$inject = ['BaseInputController'];

function atInputCheckbox (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputCheckbox'],
        templateUrl: pathService.getPartialPath('components/input/checkbox'),
        controller: AtInputCheckboxController,
        controllerAs: 'vm',
        link: atInputCheckboxLink,
        scope: {
            state: '=',
            col: '@',
            tab: '@'
        }
    };
}

atInputCheckbox.$inject = ['PathService'];

export default atInputCheckbox;
