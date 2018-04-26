const templateUrl = require('~components/input/select.partial.html');

function atInputSelectLink (scope, element, attrs, controllers) {
    const [formController, inputController] = controllers;

    inputController.init(scope, element, formController);
}

function AtInputSelectController (baseInputController, eventService) {
    const vm = this || {};

    let scope;
    let element;
    let input;
    let select;

    vm.init = (_scope_, _element_, form) => {
        baseInputController.call(vm, 'input', _scope_, _element_, form);

        scope = _scope_;
        element = _element_;
        [input] = element.find('input');
        [select] = element.find('select');

        if (scope.tab === '1') {
            select.focus();
        }

        if (!scope.state._data || scope.state._data.length === 0) {
            scope.state._disabled = true;
            scope.state._placeholder = vm.strings.get('select.EMPTY_PLACEHOLDER');
        }

        vm.setListeners();
        vm.check();

        if (scope.state._value) {
            vm.updateDisplayModel();
        }
    };

    vm.setListeners = () => {
        const listeners = eventService.addListeners([
            [input, 'focus', () => select.focus],
            [select, 'mousedown', () => scope.$apply(() => { scope.open = !scope.open; })],
            [select, 'focus', () => input.classList.add('at-Input--focus')],
            [select, 'change', () => scope.$apply(() => {
                scope.open = false;
                vm.updateDisplayModel();
                vm.check();
            })],
            [select, 'blur', () => {
                input.classList.remove('at-Input--focus');
                scope.open = scope.open && false;
            }]
        ]);

        scope.$on('$destroy', () => eventService.remove(listeners));
    };

    vm.updateDisplayModel = () => {
        if (scope.state._format === 'selectFromOptions') {
            scope.displayModel = scope.state._value[1];
        } else if (scope.state._format === 'array') {
            scope.displayModel = scope.state._value;
        } else if (scope.state._format === 'objects') {
            scope.displayModel = scope.state._value[scope.state._display];
        } else if (scope.state._format === 'grouped-object') {
            scope.displayModel = scope.state._value[scope.state._display];
        } else {
            throw new Error(vm.strings.get('select.UNSUPPORTED_TYPE_ERROR'));
        }
    };
}

AtInputSelectController.$inject = ['BaseInputController', 'EventService'];

function atInputSelect () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^at-form', 'atInputSelect'],
        templateUrl,
        controller: AtInputSelectController,
        controllerAs: 'vm',
        link: atInputSelectLink,
        scope: {
            state: '=',
            col: '@',
            tab: '@'
        }
    };
}

export default atInputSelect;
