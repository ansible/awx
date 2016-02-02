/* jshint unused: vars */

export default
    [   'templateUrl', '$state', function(templateUrl, $state) {
        return {
            restrict: 'E',
            templateUrl: templateUrl('bread-crumb/bread-crumb'),
            link: function(scope, element, attrs) {

                var streamConfig = {};

                scope.showActivityStreamButton = false;

                scope.openActivityStream = function() {

                    var stateGoParams = {};

                    if(streamConfig && streamConfig.activityStream) {
                        if(streamConfig.activityStreamTarget) {
                            stateGoParams['target'] = streamConfig.activityStreamTarget;
                        }
                        if(streamConfig.activityStreamId) {
                            stateGoParams['id'] = $state.params[streamConfig.activityStreamId];
                        }
                    }

                    $state.go('activityStream', stateGoParams);
                }

                scope.$on("$stateChangeSuccess", function updateActivityStreamButton(event, toState) {

                    streamConfig = (toState && toState.data) ? toState.data : {};

                    if(streamConfig && streamConfig.activityStream) {
                        scope.showActivityStreamButton = true;
                    }
                    else {
                        scope.showActivityStreamButton = false;
                    }
                });

            }
        };
    }];
