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

        scope.pre = {};
        scope.state._edit = true;

        if (scope.state.format === 'ssh_private_key') {
            scope.ssh = true;
            scope.state._hint = scope.state._hint || DEFAULT_HINT;
            input = element.find('input')[0];
            vm.setFileListeners(textarea, input);
        }

        if (scope.state._edit) {
            scope.edit = true;
            scope.isShown = true;
            scope.buttonText = 'REPLACE';
        }

        vm.check();
    };

    vm.setFileListeners = (textarea, input) => { 
        eventService.addListener(textarea, 'dragenter', event => {
            event.stopPropagation();
            event.preventDefault();
            scope.$apply(() => scope.drag = true);
        });

        eventService.addListener(input, 'dragleave', event => {
            event.stopPropagation();
            event.preventDefault();
            scope.$apply(() => scope.drag = false);
        });

        eventService.addListener(input, 'change', event => {
            let reader = new FileReader();

            reader.onload = () => vm.readFile(reader, event);
            reader.readAsText(input.files[0]);
        });
    };

    vm.readFile = (reader, event) => {
        scope.$apply(() => {
            scope.state._value = reader.result;
            scope.drag = false
        });
    };

    vm.toggle = () => {
        if (scope.isShown) {
            scope.buttonText = 'REVERT';
            scope.pre.value = scope.state._value;
            scope.state._value = undefined;
        } else {
            scope.state._value = scope.pre.value;
            scope.buttonText = 'REPLACE';
        }

        scope.isShown = !scope.isShown;
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
