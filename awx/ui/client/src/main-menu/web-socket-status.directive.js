/* jshint unused: vars */

export default
    [   '$rootScope',
        'templateUrl',
        function($rootScope, templateUrl) {
            return {
                restrict: 'E',
                templateUrl: templateUrl('main-menu/web-socket-status'),
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
        }
    ];
