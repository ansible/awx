const templateUrl = require('~components/input/lookup.partial.html');

const DEFAULT_DEBOUNCE = 250;
const DEFAULT_KEY = 'name';

function atInputLookupLink (scope, element, attrs, controllers) {
    const formController = controllers[0];
    const inputController = controllers[1];

    if (scope.tab === '1') {
        element.find('input')[0].focus();
    }

    inputController.init(scope, element, formController);
}

function AtInputLookupController (baseInputController, $q, $state) {
    const vm = this || {};

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
        const params = {};

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
            return vm.check({ isValid: true });
        }

        return model.search({ [search.key]: scope.state._displayValue }, search.config)
            .then(found => {
                if (!found) {
                    vm.reset();

                    return;
                }

                scope[scope.state._resource] = model.get('id');
                scope.state._value = model.get('id');
                scope.state._displayValue = model.get('name');
            })
            .catch(() => vm.reset())
            .finally(() => {
                const isValid = scope.state._value !== undefined;
                const message = isValid ? '' : vm.strings.get('lookup.NOT_FOUND');

                vm.check({ isValid, message });
            });
    };

    vm.searchOnInput = () => {
        if (vm.isDebouncing) {
            vm.resetDebounce();

            return;
        }

        vm.searchAfterDebounce();
    };
}

AtInputLookupController.$inject = [
    'BaseInputController',
    '$q',
    '$state'
];

function atInputLookup () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atInputLookup'],
        templateUrl,
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

export default atInputLookup;
