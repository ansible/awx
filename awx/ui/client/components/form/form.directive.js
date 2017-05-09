function use (type, componentScope, componentElement) { 
   let vm = this;

   let component;

   switch (type) {
        case 'input':
            component = vm.trackInput(componentElement);
            break;
        case 'action':
            component = vm.trackAction(componentElement);
            break;
        default:
            throw new Error('An at-form cannot use component type:', type);
   }

   componentScope.meta = component;
}

function trackInput (componentElement) {
    let vm = this;

    let input = {
       el: componentElement,
       tabindex: vm.inputs.length + 1
    };

    if (vm.inputs.length === 0) {
       input.autofocus = true;
       componentElement.find('input').focus();
    }

    vm.inputs.push(input);

    return input;
}

function trackAction (componentElement) {
    let vm = this;

    let action = {
       el: componentElement
    };

    vm.actions.push(action);

    return action;
}

function AtFormController () {
    let vm = this;

    vm.inputs = [];
    vm.actions = [];

    vm.use = use;
    vm.trackInput = trackInput;
    vm.trackAction = trackAction;
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
