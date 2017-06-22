function atInputLookupLink (scope, element, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    scope.ns = 'lookup';
    scope[scope.ns] = { modal: {} };

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputLookupController (baseInputController, $state) {
    let vm = this || {};

    let scope;
    let modal;

    vm.init = (_scope_, element, form) => {
        baseInputController.call(vm, 'input', _scope_, element, form);

        scope = _scope_;

        scope.$watch('organization', () => {
            if (scope.organization) {
                scope.state._value = scope.organization;
                scope.state._displayValue = scope.organization_name;
            }
        });

        modal = scope.lookup.modal;

        vm.check();
    };

    vm.search = () => {
        $state.go('credentials.add.organization');
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
