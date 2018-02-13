/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import awxNetZoomWidget from './zoom.directive';

export default
    angular.module('networkZoomWidget', [])
        .directive('awxNetZoomWidget', awxNetZoomWidget);
