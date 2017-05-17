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

function AtInputSelectController (eventService) { 
    let vm = this || {};

    let scope;
    let state;
    let form;
    let input;
    let select;

    vm.init = (_form_, _scope_, elements) => {
        form = _form_;
        input = elements.input;
        select = elements.select;
        scope = _scope_;
        state = scope.state || {};

        state.required = state.required || false;
        state.isValid = state.isValid || false;
        state.disabled = state.disabled || false;

        form.use('input', scope);

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

    vm.validate = () => {
        let isValid = true;

        if (state.required && !state.value) {
            isValid = false;    
        } 
        
        if (state.validate && !state.validate(state.value)) {
            isValid = false;  
        }

        return isValid;
    };

    vm.check = () => {
        let isValid = vm.validate();

        if (isValid !== state.isValid) {
            state.isValid = isValid;
            form.check();
        }
    };
}

AtInputSelectController.$inject = ['EventService'];

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
