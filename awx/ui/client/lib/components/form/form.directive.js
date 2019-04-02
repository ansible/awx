const templateUrl = require('~components/form/form.partial.html');

function atFormLink (scope, el, attrs, controllers) {
    const formController = controllers[0];
    const form = el[0];

    scope.ns = 'form';
    scope[scope.ns] = { modal: {} };

    formController.init(scope, form);
}

function AtFormController (eventService, strings) {
    const vm = this || {};

    let scope;
    let modal;
    let form;

    vm.components = [];
    vm.state = {
        isValid: false,
        disabled: false,
        value: {},
    };

    vm.init = (_scope_, _form_) => {
        scope = _scope_;
        form = _form_;
        ({ modal } = scope[scope.ns]);

        vm.state.disabled = scope.state.disabled;
        vm.setListeners();
    };

    vm.register = (category, component) => {
        component.category = category;
        component.form = vm.state;

        if (category === 'input') {
            scope.state[component.state.id] = component.state;
        }

        vm.components.push(component);
    };

    vm.setListeners = () => {
        const listeners = eventService.addListeners([
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

    vm.getSubmitData = () => vm.components
        .filter(component => component.category === 'input')
        .reduce((values, component) => {
            if (component.state._value === undefined) {
                return values;
            }

            if (component.state._format === 'selectFromOptions') {
                values[component.state.id] = component.state._value[0];
            } else if (component.state._key && typeof component.state._value === 'object') {
                values[component.state.id] = component.state._value[component.state._key];
            } else if (component.state._group) {
                values[component.state._key] = values[component.state._key] || {};
                values[component.state._key][component.state.id] = component.state._value;
            } else {
                values[component.state.id] = component.state._value;
            }

            return values;
        }, {});

    vm.submitSecondary = () => {
        if (!vm.state.isValid) {
            return;
        }
        const data = vm.getSubmitData();
        scope.state.secondary(data);
    };

    vm.submit = () => {
        if (!vm.state.isValid) {
            return;
        }

        vm.state.disabled = true;

        const data = vm.getSubmitData();

        scope.state.save(data)
            .then(scope.state.onSaveSuccess)
            .catch(err => vm.onSaveError(err))
            .finally(() => { vm.state.disabled = false; });
    };

    vm.onSaveError = err => {
        let handled;

        if (err.status === 400) {
            handled = vm.handleValidationError(err.data);
        }

        if (err.status === 500) {
            handled = vm.handleUnexpectedError(err);
        }

        if (!handled) {
            let message;
            const title = strings.get('form.SUBMISSION_ERROR_TITLE');
            const preface = strings.get('form.SUBMISSION_ERROR_PREFACE');

            if (typeof err.data === 'object') {
                message = JSON.stringify(err.data);
            } if (_.has(err, 'data.__all__')) {
                if (typeof err.data.__all__ === 'object' && Array.isArray(err.data.__all__)) {
                    message = JSON.stringify(err.data.__all__[0]);
                } else {
                    message = JSON.stringify(err.data.__all__);
                }
            } else {
                message = err.data;
            }

            modal.show(title, `${preface}: ${message}`);
        }
    };

    vm.handleUnexpectedError = () => {
        const title = strings.get('form.SUBMISSION_ERROR_TITLE');
        const message = strings.get('form.SUBMISSION_ERROR_MESSAGE');

        modal.show(title, message);

        return true;
    };

    vm.handleValidationError = errors => {
        const errorMessageSet = vm.setValidationMessages(errors);

        if (errorMessageSet) {
            vm.check();
        }

        return errorMessageSet;
    };

    vm.setValidationMessages = (errors, errorSet) => {
        let errorMessageSet = errorSet || false;

        Object.keys(errors).forEach(id => {
            if (!Array.isArray(errors[id]) && typeof errors[id] === 'object') {
                errorMessageSet = vm.setValidationMessages(errors[id], errorMessageSet);

                return;
            }

            vm.components
                .filter(component => component.category === 'input')
                .filter(component => errors[component.state.id])
                .forEach(component => {
                    errorMessageSet = true;

                    component.state._rejected = true;
                    component.state._message = errors[component.state.id].join(' ');
                });
        });

        return errorMessageSet;
    };

    vm.validate = () => {
        let isValid = true;

        for (let i = 0; i < vm.components.length; i++) {
            if (vm.components[i].category !== 'input') {
                continue;
            }

            if (vm.components[i].state.asTag) {
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
        const isValid = vm.validate();

        if (isValid !== vm.state.isValid) {
            vm.state.isValid = isValid;
        }

        if (isValid !== scope.state.isValid) {
            scope.state.isValid = isValid;
        }
    };

    vm.deregisterInputGroup = components => {
        for (let i = 0; i < components.length; i++) {
            for (let j = 0; j < vm.components.length; j++) {
                if (components[i] === vm.components[j].state) {
                    vm.components.splice(j, 1);
                    delete scope.state[components[i].id];
                    break;
                }
            }
        }
    };
}

AtFormController.$inject = ['EventService', 'ComponentsStrings'];

function atForm () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        require: ['atForm'],
        templateUrl,
        controller: AtFormController,
        controllerAs: 'vm',
        link: atFormLink,
        scope: {
            state: '=',
            autocomplete: '@'
        }
    };
}

export default atForm;
