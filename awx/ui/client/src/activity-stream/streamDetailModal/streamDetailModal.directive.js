/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default
    [   'templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                scope: true,
                replace: true,
                templateUrl: templateUrl('activity-stream/streamDetailModal/streamDetailModal')
            };
        }
    ];
