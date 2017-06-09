function atInputSecretLink (scope, element, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputSecretController (baseInputController) {
    let vm = this || {};

    let scope;

    vm.init = (_scope_, element, form) => {
        baseInputController.call(vm, 'input', _scope_, element, form);

        scope = _scope_;

        if (!scope.state._value || scope.state._promptOnLaunch) {
            scope.type = 'password';
            scope.buttonText = 'SHOW';

            vm.toggle = vm.toggleAddState;
        } else {
            scope.type = 'password';
            scope.edit = true;
            scope.replace = false;
            scope.buttonText = 'REPLACE';

            vm.toggle = vm.toggleEditState;
        }

        vm.check();
    };

    vm.updateValue = value => {
        if (!scope.edit || scope.replace) {
            scope.state._value = scope.state._displayValue;
        }

        vm.check();
    };

    vm.toggleEditState = () => {
        scope.state._dislpayValue = '';

        if (scope.replace) {
            scope.buttonText = 'REPLACE';
            scope.state._disabled = true;
        } else {
            scope.buttonText = 'REVERT';
            scope.state._disabled = false
        }

        scope.replace = !scope.replace;
    };

    vm.toggleAddState = () => {
        if (scope.type === 'password') {
            scope.type = 'text';
            scope.buttonText = 'HIDE';
        } else {
            scope.type = 'password';
            scope.buttonText = 'SHOW';
        }
    };
}

AtInputSecretController.$inject = ['BaseInputController'];

function atInputSecret (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputSecret'],
        templateUrl: pathService.getPartialPath('components/input/secret'),
        controller: AtInputSecretController,
        controllerAs: 'vm',
        link: atInputSecretLink,
        scope: {
            state: '=',
            col: '@',
            tab: '@'
        }
    };
}

atInputSecret.$inject = ['PathService'];

export default atInputSecret;
