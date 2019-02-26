const templateUrl = require('~components/input/text.partial.html');

function atInputTextLink (scope, element, attrs, controllers) {
    const formController = controllers[0];
    const inputController = controllers[1];

    if (scope.tab === '1') {
        const el = element.find('input')[0];
        if (el) {
            el.focus();
        }
    }

    inputController.init(scope, element, formController);
}

function AtInputTextController (baseInputController) {
    const vm = this || {};

    let scope;

    vm.init = (_scope_, element, form) => {
        baseInputController.call(vm, 'input', _scope_, element, form);
        scope = _scope_;

        scope.$watch('state._value', () => vm.check());
    };

    vm.onLookupClick = () => {
        if (scope.state._onInputLookup) {
            const { id, label, required, type } = scope.state;
            scope.state._onInputLookup({ id, label, required, type });
        }
    };
}

AtInputTextController.$inject = ['BaseInputController'];

function atInputText () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputText'],
        templateUrl,
        controller: AtInputTextController,
        controllerAs: 'vm',
        link: atInputTextLink,
        scope: {
            state: '=',
            col: '@',
            tab: '@'
        }
    };
}

export default atInputText;
