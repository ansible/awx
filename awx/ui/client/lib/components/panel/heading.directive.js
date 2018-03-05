const templateUrl = require('~components/panel/heading.partial.html');

function link (scope, el, attrs, panel) {
    scope.hideDismiss = Boolean(attrs.hideDismiss);
    panel.use(scope);
}

function atPanelHeading () {
    return {
        restrict: 'EA',
        require: '^^atPanel',
        replace: true,
        transclude: true,
        templateUrl,
        link
    };
}

export default atPanelHeading;
