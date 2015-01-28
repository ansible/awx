angular.module('DashboardGraphs')
  .directive('autoSizeModule', ['$window', function($window) {

    // Adjusts the size of the module so that all modules
    // fit into a single a page; assumes there are 2 rows
    // of modules, with the available height being offset
    // by the navbar & the count summaries module
    return function(scope, element, attr) {

      function adjustSize() {
        var winHeight = $($window).height(),
        available_height = winHeight - $('#main-menu-container .navbar').outerHeight() - $('#count-container').outerHeight() - 120;
        element.height(available_height/2);
      }

      $($window).resize(adjustSize);

      element.on('$destroy', function() {
        $($window).off('resize', adjustSize);
      });

      // This makes sure count-container div is loaded
      // by controllers/Home.js before we use it
      // to determine the available window height
      scope.$on('dashboardReady', function() {
        adjustSize();
      });

    };

}]);
