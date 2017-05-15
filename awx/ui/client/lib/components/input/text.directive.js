function link (scope, el, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];
    let input = el.find('input')[0];

    inputController.init(formController, scope, input);
}

function AtInputTextController () {
    let vm = this || {};

    let state;
    let scope;
    let input;
    let form;

    vm.init = (_form_, _scope_, _input_) => {
        form = _form_;
        scope = _scope_;
        input = _input_;

        scope.config.state = scope.config.state || {};
        state = scope.config.state;

        if (scope.tab === '1') {
            input.focus();
        }

        state.isValid = state.isValid || false;
        state.message = state.message || '';
        state.required = state.required || false;

        scope.form = form.use('input', state, input);

        vm.check();
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

function atInputText (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputText'],
        templateUrl: pathService.getPartialPath('components/input/text'),
        controller: AtInputTextController,
        controllerAs: 'vm',
        link,
        scope: {
            config: '=',
            col: '@',
            tab: '@'
        }
    };
}

atInputText.$inject = ['PathService'];

export default atInputText;
