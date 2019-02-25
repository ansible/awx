const templateUrl = require('~components/form/action.partial.html');

function link (scope, element, attrs, controllers) {
    const [formController, actionController] = controllers;

    actionController.init(formController, scope);
}

function atFormActionController ($state, strings) {
    const vm = this || {};

    let form;
    let scope;

    vm.init = (_form_, _scope_) => {
        form = _form_;
        scope = _scope_;

        switch (scope.type) {
            case 'cancel':
                vm.setCancelDefaults();
                break;
            case 'save':
                vm.setSaveDefaults();
                break;
            case 'secondary':
                vm.setSecondaryDefaults();
                break;
            default:
                vm.setCustomDefaults();
        }

        form.register('action', scope);
    };

    vm.setCancelDefaults = () => {
        scope.text = strings.get('CANCEL');
        scope.fill = 'Hollow';
        scope.color = 'default';
        scope.action = () => { $state.go(scope.to || '^'); };
    };

    vm.setSaveDefaults = () => {
        scope.text = strings.get('SAVE');
        scope.fill = '';
        scope.color = 'success';
        scope.action = () => { form.submit(); };
    };

    vm.setSecondaryDefaults = () => {
        scope.text = strings.get('TEST');
        scope.fill = '';
        scope.color = 'info';
        scope.action = () => { form.submitSecondary(); };
    };
}

atFormActionController.$inject = ['$state', 'ComponentsStrings'];

function atFormAction () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^atForm', 'atFormAction'],
        templateUrl,
        controller: atFormActionController,
        controllerAs: 'vm',
        link,
        scope: {
            state: '=',
            type: '@',
            to: '@'
        }
    };
}

export default atFormAction;
