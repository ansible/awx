function atInputTextLink (scope, el, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    if (scope.tab === '1') {
        el.find('input')[0].focus();
    }

    inputController.init(formController, scope);
}

function AtInputTextController () {
    let vm = this || {};

    let scope;
    let state;
    let form;

    vm.init = (_form_, _scope_) => {
        form = _form_;
        scope = _scope_;
        state = scope.state || {};

        state.required = state.required || false;
        state.isValid = state.isValid || false;
        state.disabled = state.disabled || false;

        form.use('input', scope);

        vm.check();
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

function atInputText (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputText'],
        templateUrl: pathService.getPartialPath('components/input/text'),
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

atInputText.$inject = ['PathService'];

export default atInputText;
