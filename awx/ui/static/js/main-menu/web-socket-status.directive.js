/* jshint unused: vars */

export default ['$rootScope', function($rootScope) {
    return {
        restrict: 'E',
        templateUrl: '/static/js/main-menu/web-socket-status.partial.html',
        link: function(scope, element, attrs) {
            scope.socketHelp = $rootScope.socketHelp;
            scope.socketTip = $rootScope.socketTip;
            $rootScope.$watch('socketStatus', function(newStatus) {
                scope.socketStatus = newStatus;
            });
            $rootScope.$watch('socketTip', function(newTip) {
                scope.socketTip = newTip;
            });
        }
    };
}];
