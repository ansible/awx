/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import standardOutLogController from './standard-out-log.controller';
export default [ 'templateUrl',
    function(templateUrl) {
    return {
        scope: {
            stdoutEndpoint: '=',
            stdoutText: '=',
            jobId: '='
        },
        templateUrl: templateUrl('standard-out/log/standard-out-log'),
        restrict: 'E',
        controller: standardOutLogController,
        link: function(scope) {
            // All of our DOM related stuff will go in here

            var lastScrollTop,
                direction;

            function detectDirection() {
                var st = $('#pre-container').scrollTop();
                if (st > lastScrollTop) {
                    direction = "down";
                } else {
                    direction = "up";
                }
                lastScrollTop = st;
                return  direction;
            }

            $('#pre-container').bind('scroll', function() {
                if (detectDirection() === "up") {
                    scope.should_apply_live_events = false;
                }

                if ($(this).scrollTop() + $(this).height() === $(this).prop("scrollHeight")) {
                    scope.should_apply_live_events = true;
                }
            });
        }
    };
}];
