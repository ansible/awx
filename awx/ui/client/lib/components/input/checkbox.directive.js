const templateUrl = require('~components/input/checkbox.partial.html');

function atInputCheckboxLink (scope, element, attrs, controllers) {
    const formController = controllers[0];
    const inputController = controllers[1];

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputCheckboxController (baseInputController) {
    const vm = this || {};

    vm.init = (scope, element, form) => {
        baseInputController.call(vm, 'input', scope, element, form);
        scope.label = scope.state.label;
        scope.state.label = vm.strings.get('OPTIONS');

        vm.check();
    };
}

AtInputCheckboxController.$inject = ['BaseInputController'];

function atInputCheckbox () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputCheckbox'],
        templateUrl,
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

export default atInputCheckbox;
