function link (scope, el, attrs, controllers) {
    let formController = controllers[0];
    let actionController = controllers[1];

    actionController.init(formController, scope);
}

function atFormActionController ($state) {
    let vm = this || {};

    let form;
    let scope;

    vm.init = (_form_, _scope_) => {
        form = _form_;
        scope = _scope_;

        switch(scope.type) {
            case 'cancel':
                vm.setCancelDefaults();
                break;
            case 'save':
                vm.setSaveDefaults();
                break;
            default:
                vm.setCustomDefaults();
        }

        form.use('action', scope);
    };

    vm.setCustomDefaults = () => {
        
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

atFormAction.$inject = ['$state'];

function atFormAction (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atFormAction'],
        templateUrl: pathService.getPartialPath('components/form/action'),
        controller: atFormActionController,
        controllerAs: 'vm',
        link,
        scope: {
            state: '=',
            type: '@'
        }
    };
}

atFormAction.$inject = ['PathService'];

export default atFormAction;
