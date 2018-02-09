const templateUrl = require('~components/tabs/tab.partial.html');

function atTabLink (scope, el, attrs, controllers) {
    const groupController = controllers[0];
    const tabController = controllers[1];

    tabController.init(scope, groupController);
}

function AtTabController ($state) {
    const vm = this;

    let scope;
    let group;

    vm.init = (_scope_, _group_) => {
        scope = _scope_;
        group = _group_;

        group.register(scope);
    };

    vm.go = () => {
        if (scope.state._disabled || scope.state._active) {
            return;
        }

        if (scope.state._go) {
            $state.go(scope.state._go, scope.state._params, { reload: true });
        } else {
            group.clearActive();
            scope.state._active = true;
        }
    };
}

AtTabController.$inject = ['$state'];

function atTab () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        require: ['^^atTabGroup', 'atTab'],
        templateUrl,
        controller: AtTabController,
        controllerAs: 'vm',
        link: atTabLink,
        scope: {
            state: '='
        }
    };
}

export default atTab;
