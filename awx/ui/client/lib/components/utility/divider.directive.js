const templateUrl = require('~components/utility/divider.partial.html');

function atPanelBody () {
    return {
        restrict: 'E',
        replace: true,
        templateUrl,
        scope: false
    };
}

export default atPanelBody;
