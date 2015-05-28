/* jshint unused: vars */

export default ['$route', '$rootScope', function($route, $rootScope) {
    return {
        require: '^^mainMenu',
        link: function(scope, element, attrs, mainMenuController) {
            var routeName = attrs.linkTo;

            scope.$on('$routeChangeStart', function() {
                // any time we start a route change,
                // assume it was from the menu, and
                // close it in case it's open
                mainMenuController.close();
            });

            scope.$on('$routeChangeSuccess', function(e, nextRoute) {
                if (nextRoute.$$route.name === routeName) {
                    element.addClass('MenuItem--active');
                } else {
                    element.removeClass('MenuItem--active');
                }
                return nextRoute.$$route.name;
            });

            scope.$on('$destroy', function() {
                element.off('click.menu-item');
            });

            element.on('click', function(e) {
                mainMenuController.close();
            }, true);

        }
    };
}];
