const templateUrl = require('~components/tabs/group.partial.html');

function AtTabGroupController () {
    const vm = this;

    vm.tabs = [];

    vm.register = tab => {
        tab.active = true;

        vm.tabs.push(tab);
    };

    vm.clearActive = () => {
        vm.tabs.forEach((tab) => {
            tab.state._active = false;
        });
    };
}

function atTabGroup () {
    return {
        restrict: 'E',
        replace: true,
        require: 'atTabGroup',
        transclude: true,
        templateUrl,
        controller: AtTabGroupController,
        controllerAs: 'vm',
        scope: {
            state: '='
        }
    };
}

export default atTabGroup;
