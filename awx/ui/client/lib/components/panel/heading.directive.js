const templateUrl = require('~components/panel/heading.partial.html');

function link (scope, el, attrs, panel) {
    scope.hideDismiss = Boolean(attrs.hideDismiss);
    panel.use(scope);
}

function atPanelHeading () {
    return {
        restrict: 'E',
        require: '^^atPanel',
        replace: true,
        transclude: true,
        templateUrl,
        link,
        scope: {
            title: '@',
            badge: '@?'
        }
    };
}

export default atPanelHeading;
