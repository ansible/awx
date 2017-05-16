function AtFormController () {
    let vm = this || {};

    vm.components = [];

    vm.state = {
        isValid: false
    };

    vm.use = (type, component, el) => { 
        return vm.trackComponent(type, component, el);
    };

    vm.trackComponent = (type, component, el) => {
        let meta = {
            el,
            type,
            state: vm.state,
            disabled: false,
            tabindex: vm.components.length + 1
        };

        if (!vm.components.length) {
            el.focus();
        }

        vm.components.push(meta)

        return meta;
    };

    vm.validate = () => {
        let isValid = true;

        vm.components
            .filter(component => component.type === 'input')
            .forEach(input => {
                if (input.isValid) {
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

function link (scope, el, attrs, controller, fn) {
    //console.log(fn);
}

function atForm (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl: pathService.getPartialPath('components/form/form'),
        controller: AtFormController,
        controllerAs: 'vm',
        link, 
        scope: {
            config: '='
        }
    };
}

atForm.$inject = ['PathService'];

export default atForm;
