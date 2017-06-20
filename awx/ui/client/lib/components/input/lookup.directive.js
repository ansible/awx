function atInputLookupLink (scope, element, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    scope.ns = 'lookup';
    scope[scope.ns] = {
        modal: {},
        search: {},
        table: {}
    };

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputLookupController (baseInputController) {
    let vm = this || {};

    let scope;
    let modal;
    let search;
    let table;

    vm.init = (_scope_, element, form) => {
        baseInputController.call(vm, 'input', _scope_, element, form);

        scope = _scope_;

        modal = scope.lookup.modal;
        search = scope.lookup.search;
        table = scope.lookup.table;

        vm.check();
    };

    vm.search = () => {
        modal.show(`Select ${scope.state.label}`);
    };
}

AtInputLookupController.$inject = ['BaseInputController'];

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
