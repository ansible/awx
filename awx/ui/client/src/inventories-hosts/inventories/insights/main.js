/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import controller from './insights.controller';
import planFilter from './plan-filter';
import service from './insights.service';
import strings from './insights.strings';

export default
angular.module('insightsDashboard', [])
    .filter('planFilter', planFilter)
    .controller('InsightsController', controller)
    .service('InsightsService', service)
    .service('InsightsStrings', strings);
