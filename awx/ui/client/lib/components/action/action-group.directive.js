const templateUrl = require('~components/action/action-group.partial.html');

function atActionGroup () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        scope: {
            col: '@',
            pos: '@'
        }
    };
}

export default atActionGroup;
