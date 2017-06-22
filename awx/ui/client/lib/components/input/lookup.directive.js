function atInputLookupLink (scope, element, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputLookupController (baseInputController, $state) {
    let vm = this || {};

    let scope;

    vm.init = (_scope_, element, form) => {
        baseInputController.call(vm, 'input', _scope_, element, form);

        scope = _scope_;

        scope.$watch(scope.state._resource, () => {
            if (scope[scope.state._resource]) {
                scope.state._value = scope[scope.state._resource];
                scope.state._displayValue = scope[`${scope.state._resource}_name`];
            }
        });

        vm.check();
    };

    vm.search = () => {
        let params = {};

        if (scope.state._value) {
            params.selected = scope.state._value;
        }

        $state.go(scope.state._route, params);
    };
}

AtInputLookupController.$inject = [
    'BaseInputController',
    '$state'
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
