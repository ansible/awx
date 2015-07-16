/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 
/* jshint unused: vars */

export default ['browserData', function(browserData) {
    return {
        link: function(scope, element, attrs) {
            element
                .attr('data-browser', browserData.userAgent)
                .attr('data-platform', browserData.platform);
        }
    };
}];
