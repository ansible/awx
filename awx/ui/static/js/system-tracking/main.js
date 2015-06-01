/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './system-tracking.route';
import factScanDataService from './data-services/fact-scan-data.service';
import getDataForComparison from './data-services/get-data-for-comparison.factory';
import getModuleOptions from './data-services/get-module-options.factory';
import controller from './system-tracking.controller';
import stringOrDateFilter from './string-or-date.filter';
import shared from 'tower/shared/main';
import utilities from 'tower/shared/Utilities';
import datePicker from './date-picker/main';

export default
    angular.module('systemTracking',
                   [   'angularMoment',
                       utilities.name,
                       shared.name,
                       datePicker.name
                   ])
        .service('factScanDataService', factScanDataService)
        .factory('getDataForComparison', getDataForComparison)
        .factory('getModuleOptions', getModuleOptions)
        .filter('stringOrDate', stringOrDateFilter)
        .controller('systemTracking', controller)
        .config(['$routeProvider', function($routeProvider) {
            var url = route.route;
            delete route.route;
            $routeProvider.when(url, route);
        }]);
