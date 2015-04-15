function getMenuStylePartialUrl(style) {

    if (style !== 'default' && style !== 'minimal') {
        console.warn('main-menu: "', style, 'is not a valid menu style. Please use "default" or "minimal".');
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
        template: '<nav class="Menu Menu--main Menu--fixed-top" ng-include="menuStylePartialUrl"></nav>',
        scope: {
            style: '&menuStyle'
        },
        link: link
    };
}
