export default
    ['templateUrl', '$state', '$rootScope', 'Store', 'Empty', '$window', 'BreadCrumbService', 'i18n', '$transitions',
    function(templateUrl, $state, $rootScope, Store, Empty, $window, BreadCrumbService, i18n, $transitions) {
        return {
            restrict: 'E',
            templateUrl: templateUrl('bread-crumb/bread-crumb'),
            link: function(scope) {

                var streamConfig = {}, originalRoute;

                let init = function() {

                    scope.showActivityStreamButton = false;
                    scope.showRefreshButton = false;
                    scope.alwaysShowRefreshButton = false;
                    scope.loadingLicense = true;

                    $transitions.onSuccess({}, function updateActivityStreamButton(trans) {
                        if(trans.from() && !Empty(trans.from().name)) {
                            // Go ahead and attach the from params to the state object so that it can all be stored together

                            trans.from().fromParams = trans.params('from') ? trans.params('from') : {};
                            // Store the state that we're coming from in local storage to be accessed when navigating away from the
                            // activity stream
                            //Store('previous_state', fromState);
                        }

                        streamConfig = (trans.to() && trans.to().data) ? trans.to().data : {};

                        if(streamConfig && streamConfig.activityStream) {
                            scope.loadingLicense = false;
                            scope.activityStreamActive = (trans.to().name === 'activityStream') ? true : false;
                            scope.activityStreamTooltip = (trans.to().name === 'activityStream') ? i18n._('Hide Activity Stream') : i18n._('View Activity Stream');
                            scope.showActivityStreamButton = true;
                        }
                        else {
                            scope.showActivityStreamButton = false;
                        }

                        scope.showRefreshButton = (streamConfig && streamConfig.refreshButton) ? true : false;
                        scope.alwaysShowRefreshButton = (streamConfig && streamConfig.alwaysShowRefreshButton) ? true: false;
                    });

                    scope.loadingLicense = false;
                    scope.activityStreamActive = ($state.current.name === 'activityStream') ? true : false;
                    scope.activityStreamTooltip = ($state.current.name === 'activityStream') ? 'Hide Activity Stream' : 'View Activity Stream';
                    scope.showActivityStreamButton = ((streamConfig && streamConfig.activityStream) || $state.current.name ==='activityStream') ? true : false;

                    function onResize(){
                        BreadCrumbService.truncateCrumbs();
                    }

                    function cleanUp() {
                        angular.element($window).off('resize', onResize);
                    }

                    angular.element($window).on('resize', onResize);
                    scope.$on('$destroy', cleanUp);
                };

                init();

                scope.refresh = function() {
                    $state.go($state.current, {}, {reload: true});
                };

                scope.toggleActivityStream = function() {

                    // If the user is not already on the activity stream then they want to navigate to it
                    if(!scope.activityStreamActive) {
                        var stateGoParams = {};

                        if(streamConfig && streamConfig.activityStream) {
                            if(streamConfig.activityStreamTarget) {
                                stateGoParams.target = streamConfig.activityStreamTarget;
                                let isTemplateTarget = _.includes(['template', 'job_template', 'workflow_job_template'], streamConfig.activityStreamTarget);
                                stateGoParams.activity_search = {
                                    or__object1__in: streamConfig.activityStreamTarget,
                                    or__object2__in: streamConfig.activityStreamTarget,
                                    order_by: '-timestamp',
                                    page_size: '20',
                                };

                                if (isTemplateTarget) {
                                    stateGoParams.activity_search.or__object1__in = 'job_template,workflow_job_template';
                                    stateGoParams.activity_search.or__object2__in = 'job_template,workflow_job_template';
                                }

                                if (streamConfig.activityStreamTarget === 'job') {
                                    stateGoParams.activity_search.or__object1__in = 'job,workflow_approval';
                                    stateGoParams.activity_search.or__object2__in = 'job,workflow_approval';
                                }

                                if (streamConfig.activityStreamTarget && streamConfig.activityStreamId && !streamConfig.noActivityStreamID) {
                                    stateGoParams.activity_search[streamConfig.activityStreamTarget] = $state.params[streamConfig.activityStreamId];
                                }
                            }
                            else {
                                stateGoParams.activity_search = {
                                    order_by: '-timestamp',
                                    page_size: '20',
                                };
                            }
                            if(streamConfig.activityStreamId && !streamConfig.noActivityStreamID) {
                                stateGoParams.id = $state.params[streamConfig.activityStreamId];
                            }
                            if(stateGoParams.target === "custom_inventory_script"){
                                if ($state.params.inventory_script_id !== undefined) {
                                    stateGoParams.activity_search[streamConfig.activityStreamTarget] = $state.params.inventory_script_id;
                                    stateGoParams.id = $state.params.inventory_script_id;
                                }
                            }

                        }
                        originalRoute = $state.current;
                        $state.go('activityStream', stateGoParams);
                    }
                    // The user is navigating away from the activity stream - take them back from whence they came
                    else {
                        if(originalRoute) {
                            $state.go(originalRoute.name, originalRoute.fromParams);
                        }
                        else {
                            // If for some reason something went wrong (like local storage was wiped, etc) take the
                            // user back to the dashboard
                            $state.go('dashboard');
                        }

                    }

                };
            }
        };
    }];
