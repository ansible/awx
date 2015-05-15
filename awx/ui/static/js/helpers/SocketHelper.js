/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 */
    /**
 * @ngdoc function
 * @name helpers.function:SocketHelper
 * @description
 *  SocketHelper.js
 *
 *  Show web socket troubleshooting help
 *
 */


export default
    angular.module('SocketHelper', ['Utilities', 'FFSocketHelpDefinition', 'SafariSocketHelpDefinition' , 'ChromeSocketHelpDefinition'])

    .factory('ShowSocketHelp', ['$location', '$rootScope', 'FFSocketHelp', 'SafariSocketHelp', 'ChromeSocketHelp', 'HelpDialog', 'browserData',
    function($location, $rootScope, FFSocketHelp, SafariSocketHelp, ChromeSocketHelp, HelpDialog, browserData) {
        return function() {
            var scope = $rootScope.$new();
            scope.socketPort = $AnsibleConfig.websocket_port;
            scope.socketURL = 'https://' + $location.host() + ':' + scope.socketPort + '/';
            scope.browserName = browserData.name;

            if (browserData.name === 'Firefox') {
                HelpDialog({ defn: FFSocketHelp, scope: scope });
            }
            else if (browserData.name === 'Safari') {
                HelpDialog({ defn: SafariSocketHelp, scope: scope });
            }
            else {
                HelpDialog({ defn: ChromeSocketHelp, scope: scope });
            }
        };
    }]);
