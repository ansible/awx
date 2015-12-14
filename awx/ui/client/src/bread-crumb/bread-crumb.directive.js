/* jshint unused: vars */

export default
    [   'templateUrl', '$route', function(templateUrl, $route) {
        return {
            restrict: 'E',
            templateUrl: templateUrl('bread-crumb/bread-crumb'),
            link: function(scope, element, attrs) {
                scope.activityStreamActive = 0;

                scope.toggleActivityStreamActive = function(){
                    scope.activityStreamActive = !scope.activityStreamActive;
                }

                scope.isActive = function (path) {
                    if ($route.current && $route.current.regexp) {
                        return $route.current.regexp.test(path);
                    }
                    return false;
                };
            }
        };
    }];
