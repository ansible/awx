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
    let scope;

    vm.init = (_scope_, element, form) => {
        baseInputController.call(vm, 'input', _scope_, element, form);
        scope = _scope_;

        vm.check();
    };

    vm.onLookupClick = () => {
        if (scope.state._onInputLookup) {
            const { id, label, required, type } = scope.state;
            scope.state._onInputLookup({ id, label, required, type });
        }
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
