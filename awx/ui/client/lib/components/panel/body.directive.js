const templateUrl = require('~components/panel/body.partial.html');

function atPanelBody () {
    return {
        restrict: 'EA',
        replace: true,
        transclude: true,
        templateUrl,
        scope: {
            state: '='
        }
    };
}

export default atPanelBody;
