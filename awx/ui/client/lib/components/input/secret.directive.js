const templateUrl = require('~components/input/secret.partial.html');

function atInputSecretLink (scope, element, attrs, controllers) {
    const formController = controllers[0];
    const inputController = controllers[1];

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputSecretController (baseInputController) {
    const vm = this || {};

    let scope;

    vm.init = (_scope_, element, form) => {
        baseInputController.call(vm, 'input', _scope_, element, form);

        scope = _scope_;
        scope.type = 'password';

        if (!scope.state._value || scope.state._promptOnLaunch) {
            scope.mode = 'input';
            scope.state._buttonText = vm.strings.get('SHOW');

            vm.toggle = vm.toggleShowHide;
        } else {
            scope.mode = 'encrypted';
            scope.state._buttonText = vm.strings.get('REPLACE');
            scope.state._placeholder = vm.strings.get('ENCRYPTED');
            vm.toggle = vm.toggleRevertReplace;
        }

        vm.check();
    };

    vm.toggleRevertReplace = () => {
        scope.state._isBeingReplaced = !scope.state._isBeingReplaced;

        vm.onRevertReplaceToggle();
    };

    vm.toggleShowHide = () => {
        if (scope.type === 'password') {
            scope.type = 'text';
            scope.state._buttonText = vm.strings.get('HIDE');
        } else {
            scope.type = 'password';
            scope.state._buttonText = vm.strings.get('SHOW');
        }
    };
}

AtInputSecretController.$inject = ['BaseInputController'];

function atInputSecret () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputSecret'],
        templateUrl,
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

export default atInputSecret;
