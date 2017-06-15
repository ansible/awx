function atTabGroupLink (scope, el, attrs, controllers) {
    let groupController = controllers[0];

    groupController.init(scope, el);
}

function AtTabGroupController ($state) {
    let vm = this;

    vm.tabs = [];

    let scope;
    let el;

    vm.init = (_scope_, _el_) => {
        scope = _scope_;
        el = _el_;
    };

    vm.register = tab => {

        tab.active = true;
/*
 *        if (vm.tabs.length === 0) {
 *            tab.active = true;
 *        } else {
 *            tab.disabled = true;
 *        }
 *
 */
        vm.tabs.push(tab);
    };
}

AtTabGroupController.$inject = ['$state'];

function atTabGroup (pathService, _$animate_) {
    return {
        restrict: 'E',
        replace: true,
        require: ['atTabGroup'],
        transclude: true,
        templateUrl: pathService.getPartialPath('components/tabs/group'),
        controller: AtTabGroupController,
        controllerAs: 'vm',
        link: atTabGroupLink,
        scope: true
    };
}

atTabGroup.$inject = ['PathService'];

export default atTabGroup;
