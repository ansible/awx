/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import hostStatusBar from './host-status-bar.directive';

export default
    angular.module('hostStatusBarDirective', [])
        .directive('hostStatusBar', hostStatusBar);
