function use (type, component, el) { 
   let vm = this;

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
}

function trackInput (component, el) {
    let vm = this;

    let form = {
        state: vm.state,
        disabled: false
    };

    vm.inputs.push(component)

    return form;
}

function trackAction (component) {
    let vm = this;

    let form = {
        state: vm.state,
        disabled: false
    };

    vm.actions.push(component);

    return form;
}

function validate () {
    let vm = this;
    
    let isValid = true;

    vm.inputs.forEach(input => {
        if (!input.isValid) { 
            isValid = false;
        }
    });

    return isValid;
}

function check () {
    let vm = this;

    let isValid = vm.validate();

    if (isValid !== vm.state.isValid) {
        vm.state.isValid = isValid;
    }
}

function remove (id) {
    let vm = this;

    delete inputs[id];
}

function AtFormController () {
    let vm = this;

    vm.state = {
        isValid: false
    };

    vm.inputs = [];
    vm.actions = [];

    vm.use = use;
    vm.trackInput = trackInput;
    vm.trackAction = trackAction;
    vm.validate = validate;
    vm.check = check;
    vm.remove = remove;
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
