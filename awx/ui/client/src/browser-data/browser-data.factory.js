/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 export default ['$window', function($window) {
    var ua = $window.navigator.userAgent,
        browserName;

    var browser =
        {   userAgent: ua,
            platform: $window.navigator.platform,
            name: "Unknown Browser"
        };

    if (ua.search("MSIE") >= 0) {
        browserName = "Internet Explorer";
    }
    else if (navigator.userAgent.search("Chrome") >= 0 && navigator.userAgent.search("OPR") < 0) {
        browserName = "Chrome";
    }
    else if (navigator.userAgent.search("Firefox") >= 0) {
        browserName = "Firefox";
    }
    else if (navigator.userAgent.search("Safari") >= 0 && navigator.userAgent.search("Chrome") < 0 && navigator.userAgent.search("OPR") < 0) {
        browserName = "Safari";
    }
    else if (navigator.userAgent.search("OPR") >= 0) {
        browserName = "Opera";
    }

    browser.name = browserName;
    return browser;
}];
