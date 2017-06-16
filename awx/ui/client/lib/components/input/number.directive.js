const DEFAULT_STEP = '1';
const DEFAULT_MIN = '0';
const DEFAULT_MAX = '1000000000';
const DEFAULT_PLACEHOLDER = '';

function atInputNumberLink (scope, element, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputNumberController (baseInputController) {
    let vm = this || {};

    vm.init = (scope, element, form) => {
        baseInputController.call(vm, 'input', scope, element, form);

        scope.state._step = scope.state._step || DEFAULT_STEP;
        scope.state._min = scope.state._min || DEFAULT_MIN;
        scope.state._max = scope.state._max || DEFAULT_MAX;
        scope.state._placeholder = scope.state._placeholder || DEFAULT_PLACEHOLDER;

        vm.check();
    };
}

AtInputNumberController.$inject = ['BaseInputController'];

function atInputNumber (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputNumber'],
        templateUrl: pathService.getPartialPath('components/input/number'),
        controller: AtInputNumberController,
        controllerAs: 'vm',
        link: atInputNumberLink,
        scope: {
            state: '=',
            col: '@',
            tab: '@'
        }
    };
}

atInputNumber.$inject = ['PathService'];

export default atInputNumber;
