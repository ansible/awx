/* jshint unused: vars */

function getMenuStylePartialUrl(style) {

    if (style !== 'default' && style !== 'minimal') {
        /* jshint ignore:start */
        console.warn('main-menu: "', style, 'is not a valid menu style. Please use "default" or "minimal".');
        /* jshint ignore:end */
        style = 'default';
    }

    return '/static/js/main-menu/menu-' + style + '.partial.html';
}

function link(scope, element, attrs) {
    scope.$watch(function(scope) {
        return scope.$eval(scope.style);
    }, function(value) {
        scope.menuStylePartialUrl = getMenuStylePartialUrl(value);
    });
}

export default function() {
    return {
        restrict: 'E',
        templateUrl: '/static/js/main-menu/main-menu.partial.html',
        scope: {
            style: '&menuStyle',
            currentUser: '='
        },
        link: link
    };
}
