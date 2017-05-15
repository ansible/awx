function AtFormController () {
    let vm = this || {};

    vm.inputs = [];
    vm.actions = [];
    vm.state = {
        isValid: false
    };

    vm.use = (type, component, el) => { 
       let state;

       switch (type) {
            case 'input':
                state = vm.trackInput(component, el);
                break;
            case 'action':
                state = vm.trackAction(component, el);
                break;
            default:
                throw new Error('An at-form cannot use component type:', type);
       }

       return state;
    };

    vm.trackInput = (component, el) => {
        let form = {
            state: vm.state,
            disabled: false
        };

        vm.inputs.push(component)

        return form;
    };

    vm.trackAction = component => {
        let form = {
            state: vm.state,
            disabled: false
        };

        vm.actions.push(component);

        return form;
    };

    vm.validate = () => {
        let isValid = true;

        vm.inputs.forEach(input => {
            if (!input.isValid) { 
                isValid = false;
            }
        });

        return isValid;
    };

    vm.check = () => {
        let isValid = vm.validate();

        if (isValid !== vm.state.isValid) {
            vm.state.isValid = isValid;
        }
    };

    vm.remove = id => {
        delete inputs[id];
    };
}

function atForm (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl: pathService.getPartialPath('components/form/form'),
        controller: AtFormController,
        controllerAs: 'vm',
        scope: {
            config: '='
        }
    };
}

atForm.$inject = ['PathService'];

export default atForm;
