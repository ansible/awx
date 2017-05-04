function use (componentScope, componentElement) { 
   let vm = this;

   let input = vm.track(componentElement);

   componentScope.meta = input;
}

function track (componentElement) {
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

function controller () {
    let vm = this;

    vm.inputs = [];
    vm.use = use;
    vm.track = track;
}

function atForm (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl: pathService.getPartialPath('components/form/form'),
        controller,
        controllerAs: 'vm',
        scope: {
            config: '='
        }
    };
}

atForm.$inject = ['PathService'];

export default atForm;
