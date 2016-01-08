/* jshint unused: vars */

export default
    [   'templateUrl', '$state', function(templateUrl, $state) {
        return {
            restrict: 'E',
            templateUrl: templateUrl('bread-crumb/bread-crumb'),
            link: function(scope, element, attrs) {
                scope.activityStreamActive = 0;

                scope.toggleActivityStreamActive = function(){
                    scope.activityStreamActive = !scope.activityStreamActive;
                };

                scope.isActive = function (path) {
                    return $state.is(path);
                };
            }
        };
    }];
