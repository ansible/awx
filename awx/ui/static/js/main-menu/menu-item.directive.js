/* jshint unused: vars */

export default ['$route', '$rootScope', function($route, $rootScope) {
    return {
        link: function(scope, element, attrs) {
            var routeName = attrs.linkTo;

            scope.$watch(function() {
                return $route.current.name;
            }, function(nextRoute) {
                if (nextRoute === routeName) {
                    element.addClass('MenuItem--active');
                } else {
                    element.removeClass('MenuItem--active');
                }
            });

        }
    };
}];
