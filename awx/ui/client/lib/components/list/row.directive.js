const templateUrl = require('~components/list/row.partial.html');

function atRow () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        scope: {
            templateId: '@',
            invalid: '=',
            invalidTooltip: '='
        }
    };
}

export default atRow;
