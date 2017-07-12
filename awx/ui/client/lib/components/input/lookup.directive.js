function atInputLookupLink (scope, element, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputLookupController (baseInputController, $state, $stateParams) {
    let vm = this || {};

    let scope;

    vm.init = (_scope_, element, form) => {
        baseInputController.call(vm, 'input', _scope_, element, form);

        scope = _scope_;

        scope.$watch(scope.state._resource, vm.watchResource);
        scope.state._validate = vm.checkOnInput;

        vm.check();
    };

    vm.watchResource = () => {
        if (scope[scope.state._resource] !== scope.state._value) {
            scope.state._value = scope[scope.state._resource];
            scope.state._displayValue = scope[`${scope.state._resource}_name`];

            vm.check();
        }
    };

    vm.lookup = () => {
        let params = {};

        if (scope.state._value && scope.state._isValid) {
            params.selected = scope.state._value;
        }

        $state.go(scope.state._route, params);
    };

    vm.reset = () => {
        scope.state._value = undefined;
        scope[scope.state._resource] = undefined;
    };

    vm.checkOnInput = () => {
        if (!scope.state._touched) {
            return { isValid: true };
        }

        let result = scope.state._model.match('get', 'name', scope.state._displayValue);

        if (result) {
            scope[scope.state._resource] = result.id;
            scope.state._value = result.id;
            scope.state._displayValue = result.name;

            return { isValid: true };
        }

        vm.reset();

        return {
            isValid: false,
            message: vm.strings.get('lookup.NOT_FOUND')
        };
    };
}

AtInputLookupController.$inject = [
    'BaseInputController',
    '$state',
    '$stateParams'
];

function atInputLookup (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputLookup'],
        templateUrl: pathService.getPartialPath('components/input/lookup'),
        controller: AtInputLookupController,
        controllerAs: 'vm',
        link: atInputLookupLink,
        scope: {
            state: '=',
            col: '@',
            tab: '@'
        }
    };
}

atInputLookup.$inject = ['PathService'];

export default atInputLookup;
