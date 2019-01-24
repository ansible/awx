const templateUrl = require('~components/list/list-toolbar.partial.html');

function atListToolbar () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        scope: {
            onExpand: '=',
            onCollapse: '=',
            sortOnly: '=',
            isCollapsed: '=',
        }
    };
}

export default atListToolbar;
