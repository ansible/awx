/* jshint unused: vars */

export default
    [   '$location', 'templateUrl', '$rootScope', function($location, templateUrl, $rootScope) {
        return {
            restrict: 'E',
            templateUrl: templateUrl('main-menu/main-menu'),
            link: function(scope, element, attrs) {
                // check to see if this is the current route
                scope.isCurrentRoute = function(route) {
                    if ($location.url().split('/')[1] === route) {
                        return true;
                    } else {
                        return false;
                    }
                }

                // check to see if the current route is the currently
                // logged in user
                scope.isCurrentRouteUser = function() {
                    if ($rootScope && $rootScope.current_user) {
                        if ($location.url().split('/')[1] === 'users') {
                            if ($location.url().split('/')[2] ===                                 ($rootScope.current_user.id + "")) {
                                    return true;
                                } else {
                                    return false;
                                }
                        } else {
                            return false;
                        }
                    } else {
                        return false;
                    }
                }

                // set up the user tooltip
                $rootScope.$on('current_user', function(user) {
                    scope.currentUserTip = "Logged in as " + user.un;
                });

                // set up things for the socket notification
                scope.socketHelp = $rootScope.socketHelp;
                scope.socketTip = $rootScope.socketTip;
                $rootScope.$watch('socketStatus', function(newStatus) {
                    scope.socketStatus = newStatus;
                    scope.socketIconClass = "icon-socket-" + scope.socketStatus;
                });
                $rootScope.$watch('socketTip', function(newTip) {
                    scope.socketTip = newTip;
                });

                // default the mobile menu as hidden
                scope.isHiddenOnMobile = true;
                // set up the click function to toggle mobile menu
                scope.toggleMenu = function() {
                    if (scope.isHiddenOnMobile) {
                        scope.isHiddenOnMobile = false;
                    } else {
                        scope.isHiddenOnMobile = true;
                    }
                }
                // if the user clicks outside of the mobile menu,
                // close it if it's open
                $("body").on('click', function(e) {
                    e.stopPropagation();
                    if ($(e.target).parents(".MainMenu").length === 0) {
                        scope.isHiddenOnMobile = true;
                    }
                });
                // close the menu when the user clicks a link to a different route
                scope.$on('$locationChangeStart', function(event) {
                    scope.isHiddenOnMobile = true;
                });
            }
        };
    }];
