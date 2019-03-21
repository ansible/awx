const templateUrl = require('~components/list/list-toolbar.partial.html');

function AtListToolbar (strings) {
    const vm = this || {};
    vm.strings = strings;
}

AtListToolbar.$inject = ['ComponentsStrings'];

function atListToolbar () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        scope: {
            onExpand: '=',
            onCollapse: '=',
            isCollapsed: '=',
            onSort: '<',
            sortOnly: '=',
            sortOptions: '<',
            sortValue: '<'
        },
        controller: AtListToolbar,
        controllerAs: 'vm'
    };
}

export default atListToolbar;
