const templateUrl = require('~components/input/textarea.partial.html');

function atInputTextareaLink (scope, element, attrs, controllers) {
    const formController = controllers[0];
    const inputController = controllers[1];

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputTextareaController (baseInputController) {
    const vm = this || {};

    vm.init = (scope, element, form) => {
        baseInputController.call(vm, 'input', scope, element, form);

        vm.check();
    };
}

AtInputTextareaController.$inject = ['BaseInputController'];

function atInputTextarea () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputTextarea'],
        templateUrl,
        controller: AtInputTextareaController,
        controllerAs: 'vm',
        link: atInputTextareaLink,
        scope: {
            state: '=',
            col: '@',
            tab: '@'
        }
    };
}

export default atInputTextarea;
