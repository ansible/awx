/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import hostStatusBarController from './host-status-bar.controller';
export default [ 'templateUrl',
    function(templateUrl) {
    return {
        scope: {
            jobData: '='
        },
        templateUrl: templateUrl('job-results/host-status-bar/host-status-bar'),
        restrict: 'E',
        // controller: standardOutLogController,
        link: function(scope) {
            // All of our DOM related stuff will go in here

        }
    }
}];
