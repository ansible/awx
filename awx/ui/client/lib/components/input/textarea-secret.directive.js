const DEFAULT_HINT = 'HINT: Drag and drop an SSH private key file on the field below.';

function atInputTextareaSecretLink (scope, element, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    if (scope.tab === '1') {
        element.find('textarea')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputTextareaSecretController (baseInputController, eventService) {
    let vm = this || {};

    let scope;
    let textarea;
    let container;
    let input;

    vm.init = (_scope_, element, form) => {
        baseInputController.call(vm, 'input', _scope_, element, form);

        scope = _scope_;
        textarea = element.find('textarea')[0];
        container = element[0];

        if (scope.state.format === 'ssh_private_key') {
            scope.ssh = true;
            scope.state._hint = scope.state._hint || DEFAULT_HINT;
            input = element.find('input')[0];
        }

        if (scope.state._value) {
            scope.state._buttonText = 'REPLACE';
            scope.state._placeholder = 'ENCRYPTED';
        } else {
            if (scope.state.format === 'ssh_private_key') {
                vm.listeners = vm.setFileListeners(textarea, input);
                scope.state._displayHint = true;
            }
        }

        vm.check();
    };

    vm.toggle = () => {
        vm.toggleRevertReplace();

        if (scope.state._isBeingReplaced) {
            scope.state._placeholder = '';
            scope.state._displayHint = true;
            vm.listeners = vm.setFileListeners(textarea, input);
        } else {
            scope.state._displayHint = false;
            scope.state._placeholder = 'ENCRYPTED';
            eventService.remove(vm.listeners);
        }
    };

    vm.setFileListeners = (textarea, input) => { 
        return eventService.addListeners([
            [textarea, 'dragenter', event => {
                event.stopPropagation();
                event.preventDefault();
                scope.$apply(() => scope.drag = true);
            }],

            [input, 'dragleave', event => {
                event.stopPropagation();
                event.preventDefault();
                scope.$apply(() => scope.drag = false);
            }],

            [input, 'change', event => {
                let reader = new FileReader();

                reader.onload = () => vm.readFile(reader, event);
                reader.readAsText(input.files[0]);
            }]
        ]);
    };

    vm.readFile = (reader, event) => {
        scope.$apply(() => {
            scope.state._value = reader.result;
            vm.check();
            scope.drag = false
            input.value = '';
        });
    };
}

AtInputTextareaSecretController.$inject = ['BaseInputController', 'EventService'];

function atInputTextareaSecret (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputTextareaSecret'],
        templateUrl: pathService.getPartialPath('components/input/textarea-secret'),
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

atInputTextareaSecret.$inject = ['PathService'];

export default atInputTextareaSecret;
