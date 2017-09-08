const templateUrl = require('@components/tabs/group.partial.html');

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

        vm.tabs.push(tab);
    };
}

AtTabGroupController.$inject = ['$state'];

function atTabGroup () {
    return {
        restrict: 'E',
        replace: true,
        require: ['atTabGroup'],
        transclude: true,
        templateUrl,
        controller: AtTabGroupController,
        controllerAs: 'vm',
        link: atTabGroupLink,
        scope: {
            state: '='
        }
    };
}

export default atTabGroup;
