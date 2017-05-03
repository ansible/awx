function track (element) { 
   let vm = this;

   let input = {
       el: element,
       tabindex: vm.form.inputs.length + 1,
       autofocus: vm.form.inputs.length === 0
   };

   vm.form.inputs.push(input);

   return input;
}

function controller () {
    let vm = this;

    vm.form = {
        inputs: []
    };

    vm.track = track;
}

function atForm () {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl: 'static/partials/components/form/form.partial.html',
        controller,
        controllerAs: 'vm',
        scope: {
            config: '='
        }
    };
}

export default atForm;
