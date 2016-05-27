export default
    [   'templateUrl', '$state', 'FeaturesService', 'ProcessErrors', 'Store', 'Empty', function(templateUrl, $state, FeaturesService, ProcessErrors, Store, Empty) {
        return {
            restrict: 'E',
            templateUrl: templateUrl('bread-crumb/bread-crumb'),
            link: function(scope) {

                var streamConfig = {};

                scope.showActivityStreamButton = false;
                scope.loadingLicense = true;

                scope.toggleActivityStream = function() {

                    // If the user is not already on the activity stream then they want to navigate to it
                    if(!scope.activityStreamActive) {
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
                    }
                    // The user is navigating away from the activity stream - take them back from whence they came
                    else {
                        // Pull the previous state out of local storage
                        var previousState = Store('previous_state');

                        if(previousState && !Empty(previousState.name)) {
                            $state.go(previousState.name, previousState.fromParams);
                        }
                        else {
                            // If for some reason something went wrong (like local storage was wiped, etc) take the
                            // user back to the dashboard
                            $state.go('dashboard');
                        }

                    }

                };

                scope.$on("$stateChangeSuccess", function updateActivityStreamButton(event, toState, toParams, fromState, fromParams) {

                    if(fromState && !Empty(fromState.name)) {
                        // Go ahead and attach the from params to the state object so that it can all be stored together
                        fromState.fromParams = fromParams ? fromParams : {};

                        // Store the state that we're coming from in local storage to be accessed when navigating away from the
                        // activity stream
                        Store('previous_state', fromState);
                    }

                    streamConfig = (toState && toState.data) ? toState.data : {};

                    if(streamConfig && streamConfig.activityStream) {

                        // Check to see if activity_streams is an enabled feature.  $stateChangeSuccess fires
                        // after the resolve on the state declaration so features should be available at this
                        // point.  We use the get() function call here just in case the features aren't available.
                        // The get() function will only fire off the server call if the features aren't already
                        // attached to the $rootScope.

                        FeaturesService.get()
                        .then(function() {
                            scope.loadingLicense = false;
                            scope.activityStreamActive = (toState.name === 'activityStream') ? true : false;
                            scope.showActivityStreamButton = (FeaturesService.featureEnabled('activity_streams') || toState.name === 'activityStream') ? true : false;
                            var licenseInfo = FeaturesService.getLicenseInfo();
                            scope.licenseType = licenseInfo ? licenseInfo.license_type : null;
                            if (!licenseInfo) {
                                console.warn("License info not loaded correctly"); // jshint ignore:line
                            }
                        })
                        .catch(function (response) {
                            ProcessErrors(null, response.data, response.status, null, {
                                hdr: 'Error!',
                                msg: 'Failed to get feature info. GET returned status: ' +
                                response.status
                            });
                        });

                    }
                    else {

                        scope.showActivityStreamButton = false;

                    }
                });

            }
        };
    }];
