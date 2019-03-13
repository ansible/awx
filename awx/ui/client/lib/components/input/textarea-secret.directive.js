const templateUrl = require('~components/input/textarea-secret.partial.html');

function atInputTextareaSecretLink (scope, element, attrs, controllers) {
    const [formController, inputController] = controllers;

    if (scope.tab === '1') {
        element.find('textarea')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputTextareaSecretController (baseInputController, eventService) {
    const vm = this || {};

    let scope;
    let textarea;
    let input;

    vm.init = (_scope_, element, form) => {
        baseInputController.call(vm, 'input', _scope_, element, form);

        scope = _scope_;

        [textarea] = element.find('textarea');

        if (scope.state.format === 'ssh_private_key') {
            scope.ssh = true;
            scope.state._hint = scope.state._hint || vm.strings.get('textarea.SSH_KEY_HINT');
            [input] = element.find('input');
        }

        if (scope.state._value) {
            scope.state._buttonText = vm.strings.get('REPLACE');
            scope.state._placeholder = vm.strings.get('ENCRYPTED');
        } else if (scope.state.format === 'ssh_private_key') {
            vm.listeners = vm.setFileListeners(textarea, input);
            scope.state._displayHint = true;
        }

        vm.check();

        scope.$watch('state[state._activeModel]', () => vm.check());
        scope.$watch('state._isBeingReplaced', () => vm.onIsBeingReplacedChanged());
    };

    vm.onIsBeingReplacedChanged = () => {
        if (!scope.state) return;
        if (!scope.state._touched) return;

        vm.onRevertReplaceToggle();

        if (scope.state._isBeingReplaced) {
            scope.state._placeholder = '';
            scope.state._displayHint = true;
            vm.listeners = vm.setFileListeners(textarea, input);
        } else {
            scope.state._displayHint = false;
            scope.state._placeholder = vm.strings.get('ENCRYPTED');

            if (vm.listeners) {
                eventService.remove(vm.listeners);
            }
        }
    };

    vm.setFileListeners = (textareaEl, inputEl) => eventService.addListeners([
        [textareaEl, 'dragenter', event => {
            event.stopPropagation();
            event.preventDefault();
            scope.$apply(() => { scope.drag = true; });
        }],

        [inputEl, 'dragleave', event => {
            event.stopPropagation();
            event.preventDefault();
            scope.$apply(() => { scope.drag = false; });
        }],

        [inputEl, 'change', event => {
            const reader = new FileReader();

            reader.onload = () => vm.readFile(reader, event);
            reader.readAsText(inputEl.files[0]);
        }]
    ]);

    vm.readFile = (reader) => {
        scope.$apply(() => {
            scope.state._value = reader.result;
            vm.check();
            scope.drag = false;
            input.value = '';
        });
    };

    vm.onLookupClick = () => {
        if (scope.state._onInputLookup) {
            const { id, label, required, type } = scope.state;
            scope.state._onInputLookup({ id, label, required, type });
        }
    };
}

AtInputTextareaSecretController.$inject = [
    'BaseInputController',
    'EventService',
    'ComponentsStrings'
];

function atInputTextareaSecret () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputTextareaSecret'],
        templateUrl,
        controller: AtInputTextareaSecretController,
        controllerAs: 'vm',
        link: atInputTextareaSecretLink,
        scope: {
            state: '=',
            col: '@',
            tab: '@'
        }
    };
}

export default atInputTextareaSecret;
