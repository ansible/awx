export default
    ['templateUrl', '$state', 'FeaturesService', 'ProcessErrors','$rootScope',
    function(templateUrl, $state, FeaturesService, ProcessErrors, $rootScope) {
        return {
            restrict: 'E',
            templateUrl: templateUrl('bread-crumb/bread-crumb'),
            link: function(scope) {

                var streamConfig = {};

                scope.showActivityStreamButton = false;
                scope.loadingLicense = true;

                scope.toggleActivityStream = function() {

                    var stateGoParams = {};

                    if(streamConfig && streamConfig.activityStream) {
                        if(streamConfig.activityStreamTarget) {
                            stateGoParams.target = streamConfig.activityStreamTarget;
                        }
                        if(streamConfig.activityStreamId) {
                            stateGoParams.id = $state.params[streamConfig.activityStreamId];
                        }
                    }

                    $state.go('activityStream', stateGoParams);
                };

                scope.$on("$stateChangeStart", function updateActivityStreamButton(event, toState) {

                    streamConfig = (toState && toState.data) ? toState.data : {};

                    if(streamConfig && streamConfig.activityStream) {

                        // Check to see if activity_streams is an enabled feature.  $stateChangeSuccess fires
                        // after the resolve on the state declaration so features should be available at this
                        // point.  We use the get() function call here just in case the features aren't available.
                        // The get() function will only fire off the server call if the features aren't already
                        // attached to the $rootScope.
                        var features = FeaturesService.get();
                        if(features){
                            scope.loadingLicense = false;
                            scope.activityStreamActive = (toState.name === 'activityStream') ? true : false;
                            scope.showActivityStreamButton = (FeaturesService.featureEnabled('activity_streams') || toState.name ==='activityStream') ? true : false;
                        }
                    }
                    else {

                        scope.showActivityStreamButton = false;

                    }
                });

                // scope.$on('featuresLoaded', function(){
                $rootScope.featuresConfigured.promise.then(function(features){
                    // var features = FeaturesService.get();
                    if(features){
                        scope.loadingLicense = false;
                        scope.activityStreamActive = ($state.name === 'activityStream') ? true : false;
                        scope.showActivityStreamButton = (FeaturesService.featureEnabled('activity_streams') || $state.name ==='activityStream') ? true : false;
                    }
                });
            }
        };
    }];
