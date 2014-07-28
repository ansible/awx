/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  SocketHelper.js
 *
 *  Show web socket troubleshooting help
 *
 */

'use strict';

angular.module('SocketHelper', ['Utilities', 'FFSocketHelpDefinition', 'SafariSocketHelpDefinition' , 'ChromeSocketHelpDefinition'])

.factory('ShowSocketHelp', ['$location', '$rootScope', 'FFSocketHelp', 'SafariSocketHelp', 'ChromeSocketHelp', 'HelpDialog',
function($location, $rootScope, FFSocketHelp, SafariSocketHelp, ChromeSocketHelp, HelpDialog) {
    return function() {
        var scope = $rootScope.$new();
        scope.socketPort = $AnsibleConfig.websocket_port;
        scope.socketURL = 'https://' + $location.host() + ':' + scope.socketPort + '/';
        if ($rootScope.browser === "FF") {
            scope.browserName = "Firefox";
            HelpDialog({ defn: FFSocketHelp, scope: scope });
        }
        else if ($rootScope.browser === "SAFARI") {
            scope.browserName = "Safari";
            HelpDialog({ defn: SafariSocketHelp, scope: scope });
        }
        else {
            if ($rootScope.browser === "MSIE") {
                scope.browserName = "Internet Explorer";
            }
            else if ($rootScope.browser === "CHROME") {
                scope.browserName = "Chrome";
            }
            else if ($rootScope.browser === "OPERA") {
                scope.browserName = "Opera";
            }
            HelpDialog({ defn: ChromeSocketHelp, scope: scope });
        }
    };
}]);