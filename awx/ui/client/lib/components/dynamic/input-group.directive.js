function link (scope, el, attrs, controllers) {
    let dynamicController = controllers[0];

    dynamicController.init(scope);
}

function atDynamicInputGroupController () {
    let vm = this || {};

    let state;
    let scope;
    let input;
    let form;

    vm.init = (_scope_) => {
        scope = _scope_;
        console.log(scope.watch);
        // scope.form = form.use('input', state);
    };
}

function atDynamicInputGroup (pathService) {
    return {
        restrict: 'E',
        replace: true,
        require: ['atDynamicInputGroup'],
        templateUrl: pathService.getPartialPath('components/dynamic/input-group'),
        controller: atDynamicInputGroupController,
        controllerAs: 'vm',
        link,
        scope: {
            config: '=',
            watch: '='
        }
    };
}

atDynamicInputGroup.$inject = ['PathService'];

export default atDynamicInputGroup;
