function atInputSelectLink (scope, el, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];
    let elements = {
        input: el.find('input')[0],
        select: el.find('select')[0]
    };

    if (scope.tab === '1') {
        elements.select.focus();
    }

    inputController.init(formController, scope, elements);
}

function AtInputSelectController (baseInputController, eventService) { 
    let vm = this || {};

    let scope;
    let input;
    let select;

    vm.init = (form, _scope_, elements) => {
        baseInputController.call(vm, 'input', _scope_, form);

        scope = _scope_;
        input = elements.input;
        select = elements.select;

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
