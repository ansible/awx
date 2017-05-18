function atInputTextareaLink (scope, el, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    if (scope.tab === '1') {
        el.find('input')[0].focus();
    }

    inputController.init(scope, formController);
}

function AtInputTextareaController (baseInputController) {
    let vm = this || {};

    vm.init = (scope, form) => {
        baseInputController.call(vm, 'input', scope, form);

        vm.check();
    };
}

AtInputTextareaController.$inject = ['BaseInputController'];

function atInputTextarea (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputTextarea'],
        templateUrl: pathService.getPartialPath('components/input/textarea'),
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

atInputTextarea.$inject = ['PathService'];

export default atInputTextarea;
