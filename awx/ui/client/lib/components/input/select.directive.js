function atInputSelectLink (scope, element, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    if (scope.tab === '1') {
        elements.select.focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputSelectController (baseInputController, eventService) { 
    let vm = this || {};

    let scope;
    let element;
    let input;
    let select;

    vm.init = (_scope_, _element_, form) => {
        baseInputController.call(vm, 'input', _scope_, _element_, form);

        scope = _scope_;
        element = _element_;
        input = element.find('input')[0];
        select = element.find('select')[0];

        vm.setListeners();
        vm.check();
    };

    vm.setListeners = () => {
        let listeners = eventService.addListeners([
            [input, 'focus', () => select.focus],
            [select, 'mousedown', () => scope.$apply(() => scope.open = !scope.open)],
            [select, 'focus', () => input.classList.add('at-Input--focus')],
            [select, 'change', () => scope.$apply(() => {
                scope.open = false;
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
        if (scope.state._format === 'array') {
            scope.displayModel = scope.state._data[scope.state._value];
        } else if (scope.state._format === 'grouped-object') {
            scope.displayModel = scope.state._value[scope.state._display];
        } else {
            throw new Error('Unsupported display model type');
        }
    };
}

AtInputSelectController.$inject = ['BaseInputController', 'EventService'];

function atInputSelect (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^at-form', 'atInputSelect'],
        templateUrl: pathService.getPartialPath('components/input/select'),
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

atInputSelect.$inject = ['PathService'];

export default atInputSelect;
