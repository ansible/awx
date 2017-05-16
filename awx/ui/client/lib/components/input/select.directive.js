function link (scope, el, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];
    let input = el.find('input')[0];
    let select = el.find('select')[0];

    inputController.init(formController, scope, input, select);
}

function AtInputSelectController (eventService) { 
    let vm = this || {};

    let scope;
    let state;
    let input;
    let select;
    let form;

    vm.init = (_form_, _scope_, _input_, _select_) => {
        form = _form_;
        scope = _scope_;
        input = _input_;
        select = _select_;

        scope.config.state = scope.config.state || {};
        state = scope.config.state;

        state.isValid = state.isValid || false;
        state.message = state.message || '';
        state.required = scope.config.options.required || false;

        scope.form = form.use('input', state, input);

        vm.setListeners();
        vm.check();
    };

    vm.setListeners = () => {
        let listeners = eventService.addListeners(scope, [
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
        } else if (state.validate && !state.validate(scope.config.input)) {
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
        link,
        scope: {
            config: '=',
            col: '@',
            tab: '@'
        }
    };
}

atInputSelect.$inject = ['PathService'];

export default atInputSelect;
