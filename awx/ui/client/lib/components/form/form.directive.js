function AtFormController () {
    let vm = this || {};

    vm.components = [];

    vm.state = {
        isValid: false
    };

    vm.use = (type, component, el) => { 
        return vm.trackComponent(type, component, el);
    };

    vm.trackComponent = (type, component) => {
        component.type = type;
        component.form = vm.state;

        vm.components.push(component)
    };

    vm.validate = () => {
        let isValid = true;

        for (let i = 0; i < vm.components.length; i++) {
            if (vm.components[i].type !== 'input') {
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

    vm.remove = id => {
        delete inputs[id];
    };
}

function atForm (pathService) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl: pathService.getPartialPath('components/form/form'),
        controller: AtFormController,
        controllerAs: 'vm',
        scope: {
            state: '='
        }
    };
}

atForm.$inject = ['PathService'];

export default atForm;
