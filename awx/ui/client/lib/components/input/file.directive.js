const templateUrl = require('~components/input/file.partial.html');

function atInputFileLink (scope, element, attrs, controllers) {
    const formController = controllers[0];
    const inputController = controllers[1];

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputFileController (baseInputController, eventService) {
    const vm = this || {};

    let input;
    let scope;

    vm.init = (_scope_, element, form) => {
        baseInputController.call(vm, 'input', _scope_, element, form);

        scope = _scope_;
        input = element.find('input')[0]; // eslint-disable-line prefer-destructuring

        vm.listeners = vm.setFileListeners(input);

        vm.check();
    };

    vm.onButtonClick = () => {
        if (scope.state._value) {
            vm.removeFile();
        } else {
            input.click();
        }
    };

    vm.setFileListeners = inputEl => eventService.addListeners([
        [inputEl, 'change', event => vm.handleFileChangeEvent(inputEl, event)]
    ]);

    vm.handleFileChangeEvent = (element, event) => {
        if (element.files.length > 0) {
            const reader = new FileReader();

            reader.onload = () => vm.readFile(reader, event);
            reader.readAsText(element.files[0]);
        } else {
            scope.$apply(vm.removeFile);
        }
    };

    vm.readFile = (reader, event) => {
        scope.$apply(() => {
            scope.state._value = reader.result;
            scope.state._displayValue = event.target.files[0].name;

            vm.check();
        });
    };

    vm.removeFile = () => {
        delete scope.state._value;
        delete scope.state._displayValue;

        input.value = '';
    };
}

AtInputFileController.$inject = [
    'BaseInputController',
    'EventService'
];

function atInputFile () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputFile'],
        templateUrl,
        controller: AtInputFileController,
        controllerAs: 'vm',
        link: atInputFileLink,
        scope: {
            state: '=',
            col: '@',
            tab: '@'
        }
    };
}

export default atInputFile;
