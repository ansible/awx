const templateUrl = require('~components/list/row-action.partial.html');

function atRowAction () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        scope: {
            icon: '@',
            tooltip: '@'
        }
    };
}

export default atRowAction;
