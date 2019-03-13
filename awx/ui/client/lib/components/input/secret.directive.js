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
        scope.state._show = false;
        scope.state._showHideText = vm.strings.get('SHOW');

        if (!scope.state._value || scope.state._promptOnLaunch) {
            scope.mode = 'input';
        } else {
            scope.mode = 'encrypted';
            scope.state._placeholder = vm.strings.get('ENCRYPTED');
            scope.state._buttonText = vm.strings.get('REPLACE');
        }

        vm.check();
    };

    vm.toggleRevertReplace = () => {
        scope.state._isBeingReplaced = !scope.state._isBeingReplaced;

        vm.onRevertReplaceToggle();

        if (scope.state._isBeingReplaced) {
            if (scope.type !== 'password') {
                vm.toggleShowHide();
            }
        }
    };

    vm.toggleShowHide = () => {
        if (scope.type === 'password') {
            scope.type = 'text';
            scope.state._show = true;
            scope.state._showHideText = vm.strings.get('HIDE');
        } else {
            scope.type = 'password';
            scope.state._show = false;
            scope.state._showHideText = vm.strings.get('SHOW');
        }
    };

    vm.onLookupClick = () => {
        if (scope.state._onInputLookup) {
            const { id, label, required, type } = scope.state;
            scope.state._onInputLookup({ id, label, required, type });
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
