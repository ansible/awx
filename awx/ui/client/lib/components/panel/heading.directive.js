const templateUrl = require('~components/panel/heading.partial.html');

function link (scope, el, attrs, panel) {
    panel.use(scope);
}

function atPanelHeading () {
    return {
        restrict: 'E',
        require: '^^atPanel',
        replace: true,
        transclude: true,
        templateUrl,
        link
    };
}

export default atPanelHeading;
