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
    let input;

    vm.init = (_scope_, element, form) => {
        baseInputController.call(vm, 'input', _scope_, element, form);

        scope = _scope_;
        textarea = element.find('textarea')[0];

        if (scope.state.format === 'ssh_private_key') {
            scope.ssh = true;
            scope.state._hint = scope.state._hint || DEFAULT_HINT;
            input = element.find('input')[0];
            vm.setFileListeners(textarea, input);
        } else {
            scope.isShown = true;
            scope.buttonText = 'HIDE';
        }

        vm.check();
    };

    vm.setFileListeners = (textarea, input) => { 
        textarea
        let eventNames = [
            'drag',
            'dragstart',
            'dragend',
            'dragover',
            'dragenter',
            'dragleave',
            'drop'
        ];

        eventService.addListener(textarea, 'dragenter', event => {
            console.log('enter');
            scope.drag = true;
        });

        eventService.addListener(input, ['dragleave', 'dragover'], event => {
            console.log('exit');
            scope.drag = false;
        });

        eventService.addListener(input, 'drop', event => {
            vm.readFile(event.originalEvent.dataTransfer.files);
        });

        eventService.addListener(input, eventNames, event => {
            event.stopPropagation();
        });
    };

    vm.readFile = () => {
        console.log(file);
    };

    vm.toggle = () => {
        if (scope.isShown) {
            scope.buttonText = 'SHOW';
        } else {
            scope.buttonText = 'HIDE';
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
