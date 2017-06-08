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
            input = element.find('input')[0];
        }

        if (scope.state._value) {
            scope.edit = true;
            scope.replace = false;
            scope.buttonText = 'REPLACE';
        } else {
            scope.state._hint = scope.state._hint || DEFAULT_HINT;
            vm.listeners = vm.setFileListeners(textarea, input);
        }


        vm.updateModel();
    };

    vm.updateModel = (value) => {
        if (!scope.edit || scope.replace) {
            scope.state._value = scope.displayModel;
        }

        vm.check();
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
            scope.displayModel = reader.result;
            vm.updateModel();
            scope.drag = false
            input.value = '';
        });
    };

    vm.toggle = () => {
        scope.displayModel = undefined;

        if (scope.replace) {
            scope.buttonText = 'REPLACE';
            scope.state._hint = '';
            eventService.remove(vm.listeners);
        } else {
            scope.buttonText = 'REVERT';
            scope.state._hint = scope.state._hint || DEFAULT_HINT;
            vm.listeners = vm.setFileListeners(textarea, input);
        }

        scope.replace = !scope.replace;
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
