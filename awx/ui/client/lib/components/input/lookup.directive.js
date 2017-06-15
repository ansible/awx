function atInputLookupLink (scope, element, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputLookupController (baseInputController) {
    let vm = this || {};

    vm.lookup = {};

    vm.init = (scope, element, form) => {
        baseInputController.call(vm, 'input', scope, element, form);

        vm.lookup.modal = {
            title: 'Select Organization',
            buttons: [
                {
                    type: 'cancel'
                },
                {
                    type: 'select'
                }
            ]
        };

        vm.lookup.search = {
            placeholder: 'test'
        };

        vm.lookup.table = {

        };

        vm.check();
    };

    vm.search = () => {
        vm.modal.show('test');
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
