/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import jobResultsStdOut from './job-results-stdout.directive';

export default
    angular.module('jobResultStdOutDirective', [])
        .directive('jobResultsStandardOut', jobResultsStdOut);
