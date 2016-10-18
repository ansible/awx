/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import hostStatusBarController from './host-status-bar.controller';
export default [ 'templateUrl',
    function(templateUrl) {
    return {
        scope: true,
        templateUrl: templateUrl('job-results/job-results-stdout/job-results-stdout'),
        restrict: 'E',
        // controller: jobResultsStdOutController,
        link: function(scope) {

        }
    };
}];
