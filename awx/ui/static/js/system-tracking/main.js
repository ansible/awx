import route from './system-tracking.route';
import singleHostDataService from './single-host-data.service';
import factDataServiceFactory from './fact-data-service.factory';
import controller from './system-tracking.controller';
import stringOrDateFilter from './string-or-date.filter';
import xorObjects from './xor-objects.factory';
import formatResults from './format-results.factory';
import compareHosts from './compare-hosts.factory';

export default
    angular.module('systemTracking',
                   [    'angularMoment'
                   ])
        .factory('factDataServiceFactory', factDataServiceFactory)
        .service('singleHostDataService', singleHostDataService)
        .factory('xorObjects', xorObjects)
        .factory('formatResults', formatResults)
        .factory('compareHosts', compareHosts)
        .filter('stringOrDate', stringOrDateFilter)
        .controller('systemTracking', controller)
        .config(['$routeProvider', function($routeProvider) {
            var url = route.route;
            delete route.route;
            $routeProvider.when(url, route);
        }]);



