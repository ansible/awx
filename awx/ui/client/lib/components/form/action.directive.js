function link (scope, element, attrs, controllers) {
    let formController = controllers[0];
    let actionController = controllers[1];

    actionController.init(formController, element, scope);
}

function atFormActionController ($state) {
    let vm = this || {};

    let element;
    let form;
    let scope;

    vm.init = (_form_, _element_, _scope_) => {
        form = _form_;
        element = _element_;
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

        form.register('action', scope);
    };

    vm.setCustomDefaults = () => {
        
    };

    vm.setCancelDefaults = () => {
        scope.text = 'CANCEL';
        scope.fill = 'Hollow';
        scope.color = 'default';
        scope.action = () => $state.go('^');
    };

    vm.setSaveDefaults = () => {
        scope.text = 'SAVE';
        scope.fill = '';
        scope.color = 'success';
        scope.action = () => form.submit();
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
