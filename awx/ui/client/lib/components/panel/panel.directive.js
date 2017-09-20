const templateUrl = require('~components/panel/panel.partial.html');

function atPanelLink (scope, el, attrs, controller) {
    const panelController = controller;

    panelController.init(scope);
}

function AtPanelController ($state) {
    const vm = this;

    let scope;

    vm.init = (_scope_) => {
        scope = _scope_;
    };

    vm.dismiss = () => {
        $state.go(scope.onDismiss || '^');
    };

    vm.use = child => {
        child.dismiss = vm.dismiss;
    };
}

AtPanelController.$inject = ['$state'];

function atPanel () {
    return {
        restrict: 'E',
        replace: true,
        require: 'atPanel',
        transclude: true,
        templateUrl,
        controller: AtPanelController,
        controllerAs: 'vm',
        link: atPanelLink,
        scope: {
            state: '=',
            onDismiss: '@'
        }
    };
}

export default atPanel;
