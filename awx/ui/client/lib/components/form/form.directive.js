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
        isValid: false
    };

    vm.init = (_scope_, _form_) => {
        scope = _scope_;
        form = _form_;

        vm.setListeners();
    };

    vm.register = (category, component, el) => { 
        component.category = category;
        component.form = vm.state;

        if (category === 'input') {
            component.state.index = vm.components.length;
        }

        vm.components.push(component)
    };

    vm.setListeners = () => {
        let listeners = eventService.addListeners([
            [form, 'keypress', vm.submitOnEnter]
        ]);

        scope.$on('$destroy', () => eventService.remove(listeners));
    };

    vm.submitOnEnter = event => {
        if (event.key !== 'Enter') {
            return;
        }

        event.preventDefault();
        
        vm.submit();
    };

    vm.submit = event => {
        if (!vm.state.isValid) {
            return;
        }

        console.log('submit', event, vm.components);
    };

    vm.validate = () => {
        let isValid = true;

        for (let i = 0; i < vm.components.length; i++) {
            if (vm.components[i].category !== 'input') {
                continue;
            }

            if (!vm.components[i].state.isValid) {
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

    vm.deregisterDynamicComponents = components => {
        let offset = 0;

        components.forEach(component => {
            vm.components.splice(component.index - offset, 1);
            offset++;
        });
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
