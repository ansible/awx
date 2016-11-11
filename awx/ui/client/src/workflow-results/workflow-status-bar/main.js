/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import workflowStatusBar from './workflow-status-bar.directive';

export default
    angular.module('workflowStatusBarDirective', [])
        .directive('workflowStatusBar', workflowStatusBar);
