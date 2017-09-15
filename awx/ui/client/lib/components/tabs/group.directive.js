const templateUrl = require('~components/tabs/group.partial.html');

function AtTabGroupController () {
    const vm = this;

    vm.tabs = [];

    vm.register = tab => {
        tab.active = true;

        vm.tabs.push(tab);
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
