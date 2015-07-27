/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './system-tracking.route';
import controller from './system-tracking.controller';
import shared from '../shared/main';
import utilities from '../shared/Utilities';

import datePicker from './date-picker/main';
import dataServices from './data-services/main';
import factDataTable from './fact-data-table/main';

export default
    angular.module('systemTracking',
                   [   utilities.name,
                       shared.name,
                       datePicker.name,
                       factDataTable.name,
                       dataServices.name
                   ])
        .controller('systemTracking', controller)
        .config(['$routeProvider', function($routeProvider) {
            var url = route.route;
            delete route.route;
            $routeProvider.when(url, route);
        }]);
