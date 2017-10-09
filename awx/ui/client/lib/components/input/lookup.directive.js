const DEFAULT_DEBOUNCE = 250;
const DEFAULT_KEY = 'name';

function atInputLookupLink (scope, element, attrs, controllers) {
    let formController = controllers[0];
    let inputController = controllers[1];

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputLookupController (baseInputController, $q, $state) {
    let vm = this || {};

    let scope;
    let model;
    let search;

    vm.init = (_scope_, element, form) => {
        baseInputController.call(vm, 'input', _scope_, element, form);

        scope = _scope_;
        model = scope.state._model;
        scope.state._debounce = scope.state._debounce || DEFAULT_DEBOUNCE;
        search = scope.state._search || {
            key: DEFAULT_KEY,
            config: {
                unique: true
            }
        };

        scope.$watch(scope.state._resource, vm.watchResource);

        vm.check();
    };

    vm.watchResource = () => {
        if (!scope[scope.state._resource]) {
            return;
        }

        if (scope[scope.state._resource] !== scope.state._value) {
            scope.state._displayValue = scope[`${scope.state._resource}_name`];

            vm.search();
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

    vm.searchAfterDebounce = () => {
        vm.isDebouncing = true;

        vm.debounce = window.setTimeout(() => {
            vm.isDebouncing = false;
            vm.search();
        }, scope.state._debounce);
    };

    vm.resetDebounce = () => {
        clearTimeout(vm.debounce);
        vm.searchAfterDebounce();
    };

    vm.search = () => {
        scope.state._touched = true;

        if (scope.state._displayValue === '' && !scope.state._required) {
            scope.state._value = null;
            return vm.check({ isValid: true });
        }

        return model.search({ [search.key]: scope.state._displayValue }, search.config)
            .then(found => {
                if (!found) {
                    return vm.reset();
                }

                scope[scope.state._resource] = model.get('id');
                scope.state._value = model.get('id');
                scope.state._displayValue = model.get('name');
            })
            .catch(() => vm.reset())
            .finally(() => {
                let isValid = scope.state._value !== undefined;
                let message = isValid ? '' : vm.strings.get('lookup.NOT_FOUND');

                vm.check({ isValid, message });
            });
    };

    vm.searchOnInput = () => {
        if (vm.isDebouncing) {
            return vm.resetDebounce();
        }

        vm.searchAfterDebounce();
    };
}

AtInputLookupController.$inject = [
    'BaseInputController',
    '$q',
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
