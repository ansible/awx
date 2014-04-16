/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobTemplatesHelper
 *
 *  Routines shared by job related controllers
 *
 */

'use strict';

angular.module('JobTemplatesHelper', ['Utilities'])

/*
 * Add bits to $scope for handling callback url help
 *
 */
.factory('CallbackHelpInit', ['$location', 'GetBasePath', function($location, GetBasePath) {
    return function(params) {
        
        var scope = params.scope;
        
        // The form uses awPopOverWatch directive to 'watch' scope.callback_help for changes. Each time the
        // popover is activated, a function checks the value of scope.callback_help before constructing the content.
        scope.setCallbackHelp = function() {
            scope.callback_help = "<p>With a callback URL and a host config key a host can contact Tower and request a configuration update using this job " +
                "template. The request from the host must be a POST. Here is an example using curl:</p>\n" +
                "<pre>curl --data \"host_config_key=\"" + scope.example_config_key + "\" " +
                scope.callback_server_path + GetBasePath('job_templates') + scope.example_template_id + "/callback/</pre>\n" +
                "<p>Note the requesting host must be defined in the inventory associated with the job template. If Tower fails to " +
                "locate the host, the request will be denied.</p>" +
                "<p>Successful requests create an entry on the Jobs page, where results and history can be viewed.</p>";
        };

        // The md5 helper emits NewMD5Generated whenever a new key is available
        if (scope.removeNewMD5Generated) {
            scope.removeNewMD5Generated();
        }
        scope.removeNewMD5Generated = scope.$on('NewMD5Generated', function() {
            scope.configKeyChange();
        });

        // Fired when user enters a key value
        scope.configKeyChange = function() {
            scope.example_config_key = scope.host_config_key;
            scope.setCallbackHelp();
        };

        // Set initial values and construct help text
        scope.callback_server_path = $location.protocol() + '://' + $location.host() + (($location.port()) ? ':' + $location.port() : '');
        scope.example_config_key = '5a8ec154832b780b9bdef1061764ae5a';
        scope.example_template_id = 'N';
        scope.setCallbackHelp();
    };

}]);


