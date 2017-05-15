function link (scope, el, attrs, controllers) {
    let formController = controllers[0];
    let actionController = controllers[1];

    actionController.init(formController, scope);
}

function atActionController ($state) {
    let vm = this || {};

    let form;
    let scope;
    let el;
    let state;

    vm.init = (_form_, _scope_) => {
        form = _form_;
        scope = _scope_;

        scope.config = scope.config || {};
        scope.config.state = scope.config.state || {};

        state = scope.config.state;

        scope.form = form.use('action', state);

        switch(scope.type) {
            case 'cancel':
                vm.setCancelDefaults();
                break;
            case 'save':
                vm.setSaveDefaults();
                break;
            default:
                // TODO: custom type (when needed)
        }
    };

    vm.setCancelDefaults = () => {
        scope.text = 'CANCEL';
        scope.fill = 'Hollow';
        scope.color = 'white';
        scope.action = () => $state.go('^');
    };

    vm.setSaveDefaults = () => {
        scope.text = 'SAVE';
        scope.fill = '';
        scope.color = 'green';
    };
}

atActionController.$inject = ['$state'];

function atAction (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atAction'],
        templateUrl: pathService.getPartialPath('components/action/action'),
        controller: atActionController,
        controllerAs: 'vm',
        link,
        scope: {
            type: '@'
        }
    };
}

atAction.$inject = ['PathService'];

export default atAction;
