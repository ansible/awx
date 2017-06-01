function atFormLink (scope, el, attrs, controllers) {
    let formController = controllers[0];
    let form = el[0];

    formController.init(scope, form);
}

function AtFormController (eventService) {
    let vm = this || {};

    let scope;
    let form;

    vm.components = [];
    vm.state = {
        isValid: false,
        disabled: false,
        value: {}
    };

    vm.init = (_scope_, _form_) => {
        scope = _scope_;
        form = _form_;

        vm.setListeners();
    };

    vm.register = (category, component, el) => { 
        component.category = category;
        component.form = vm.state;

        vm.components.push(component)
    };

    vm.setListeners = () => {
        let listeners = eventService.addListeners([
            [form, 'keypress', vm.submitOnEnter]
        ]);

        scope.$on('$destroy', () => eventService.remove(listeners));
    };

    vm.submitOnEnter = event => {
        if (event.key !== 'Enter' || event.srcElement.type === 'textarea') {
            return;
        }

        event.preventDefault();
        scope.$apply(vm.submit);
    };

    vm.submit = event => {
        if (!vm.state.isValid) {
            return;
        }

        vm.state.disabled = true;

        let data = vm.components
            .filter(component => component.category === 'input')
            .reduce((values, component) => {
                if (!component.state._value) {
                    return values;
                }

                if (component.state._key && typeof component.state._value === 'object') {
                    values[component.state.id] = component.state._value[component.state._key];
                } else if (component.state._group) {
                    values[component.state._key] = values[component.state._key] || {};
                    values[component.state._key][component.state.id] = component.state._value;
                } else {
                    values[component.state.id] = component.state._value;
                }

                return values;
            }, {});

        scope.state.save(data)
            .then(scope.state.created)
            .catch(err => vm.onSaveError(err))
            .finally(() => vm.state.disabled = false);
    };

    vm.onSaveError = err => {
        let handled;

        if (err.status === 400) {
            handled = vm.handleValidationErrors(err.data);
        }

        if (!handled) {
            // TODO: launch modal for unexpected error type
        }
    };

    vm.handleValidationErrors = errors => {
        let errorMessageSet = vm.setValidationMessages(errors);

        if (errorMessageSet) {
            vm.check();
        }

        return errorMessageSet;
    };

    vm.setValidationMessages = (errors, errorSet) => {
        let errorMessageSet = errorSet || false;

        for (let id in errors) {
            if (!Array.isArray(errors[id]) && typeof errors[id] === 'object') {
                errorMessageSet = vm.setValidationMessages(errors[id], errorMessageSet);
                continue;
            }

            vm.components
                .filter(component => component.category === 'input')
                .filter(component => errors[component.state.id])
                .forEach(component => {
                    errorMessageSet = true;

                    component.state._rejected = true;
                    component.state._isValid = false;
                    component.state._message = errors[component.state.id].join(' ');
                });
        }

        return errorMessageSet;
    };

    vm.validate = () => {
        let isValid = true;

        for (let i = 0; i < vm.components.length; i++) {
            if (vm.components[i].category !== 'input') {
                continue;
            }

            if (!vm.components[i].state._isValid) {
                isValid = false;
                break;
            }
        }

        return isValid;
    };

    vm.check = () => {
        let isValid = vm.validate();

        if (isValid !== vm.state.isValid) {
            vm.state.isValid = isValid;
        }
    };

    vm.deregisterInputGroup = components => {
        for (let i = 0; i < components.length; i++) {
            for (let j = 0; j < vm.components.length; j++) {
                if (components[i] === vm.components[j].state) {
                    vm.components.splice(j, 1);
                    break;
                }
            }
        }
    };
}

AtFormController.$inject = ['EventService'];

function atForm (pathService) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        require: ['atForm'],
        templateUrl: pathService.getPartialPath('components/form/form'),
        controller: AtFormController,
        controllerAs: 'vm',
        link: atFormLink,
        scope: {
            state: '='
        }
    };
}

atForm.$inject = ['PathService'];

export default atForm;
