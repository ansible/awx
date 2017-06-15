function atTabLink (scope, el, attrs, controllers) {
    let groupController = controllers[0];
    let tabController = controllers[1];

    tabController.init(scope, el, groupController);
}

function AtTabController ($state) {
    let vm = this;

    let scope;
    let el;
    let group;

    vm.init = (_scope_, _el_, _group_) => {
        scope = _scope_;
        el = _el_;
        group = _group_;

        group.register(scope);
    };

    vm.go = () => {
        if (scope.state._disabled || scope.state._active) {
            return;
        }

        $state.go(scope.state._go, scope.state._params, { reload: true });
    };
}

AtTabController.$inject = ['$state'];

function atTab (pathService, _$animate_) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        require: ['^^atTabGroup', 'atTab'],
        templateUrl: pathService.getPartialPath('components/tabs/tab'),
        controller: AtTabController,
        controllerAs: 'vm',
        link: atTabLink,
        scope: {
            state: '='
        }
    };
}

atTab.$inject = ['PathService'];

export default atTab;
