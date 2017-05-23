/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import controller from './insights.controller';
import planFilter from './plan-filter';

export default
angular.module('insightsDashboard', [])
    .filter('planFilter', planFilter)
    .controller('InsightsController', controller);
