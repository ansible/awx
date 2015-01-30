angular.module('DashboardGraphs')
.directive('autoSizeModule', ['$window', '$timeout', function($window, $timeout) {

    // Adjusts the size of the module so that all modules
    // fit into a single a page; assumes there are 2 rows
    // of modules, with the available height being offset
    // by the navbar & the count summaries module
    return function(scope, element) {

        // We need to trigger a resize on the first call
        // to this when the view things load; but we don't want
        // to trigger a global window resize for everything that
        // has an auto resize, since they'll all pick it up with
        // a single call
        var triggerResize =
            _.throttle(function() {
            $($window).resize();
        }, 1000);

        function adjustSizeInitially() {
            adjustSize();
            triggerResize();
        }

        function adjustSize() {
            var winHeight = $($window).height(),
            available_height = winHeight - $('#main-menu-container .navbar').outerHeight() - $('#count-container').outerHeight() - 120;
            element.height(available_height/2);
        }

        $($window).resize(adjustSize);

        element.on('$destroy', function() {
            $($window).off('resize', adjustSize);
        });

        // Wait a second or until dashboardReady triggers,
        // whichever comes first. The timeout handles cases
        // where dashboardReady never fires.

        var dashboardReadyTimeout = $timeout(adjustSizeInitially, 500);

        // This makes sure count-container div is loaded
        // by controllers/Home.js before we use it
        // to determine the available window height
        scope.$on('dashboardReady', function() {
            $timeout.cancel(dashboardReadyTimeout);
            adjustSizeInitially();
        });

    };

}]);
