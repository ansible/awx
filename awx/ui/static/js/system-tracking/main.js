import route from './system-tracking.route';

export default
    angular.module('systemTracking', [])
        .config(['$routeProvider', function($routeProvider) {
            var url = route.route;
            delete route.route;
            $routeProvider.when(url, route);
        }]);
