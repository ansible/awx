export default
    function CallbackHelpInit($q, $location, GetBasePath, Rest, JobTemplateForm, GenerateForm, $stateParams, ProcessErrors,
             ParseVariableString, Empty, Wait, MultiCredentialService, $rootScope) {
        return function(params) {
            var scope = params.scope;
            // checkSCMStatus, getPlaybooks, callback,
            // choicesCount = 0;

            // The form uses awPopOverWatch directive to 'watch' scope.callback_help for changes. Each time the
            // popover is activated, a function checks the value of scope.callback_help before constructing the content.
            scope.setCallbackHelp = function() {
                scope.callback_help = "<p>With a provisioning callback URL and a host config key a host can contact " + $rootScope.BRAND_NAME + " and request a configuration update using this job " +
                    "template. The request from the host must be a POST. Here is an example using curl:</p>\n" +
                    "<pre>curl --data \"host_config_key=" + scope.example_config_key + "\" " +
                    scope.callback_server_path + GetBasePath('job_templates') + scope.example_template_id + "/callback/</pre>\n" +
                    "<p>Note the requesting host must be defined in the inventory associated with the job template. If " + $rootScope.BRAND_NAME + " fails to " +
                    "locate the host, the request will be denied.</p>" +
                    "<p>Successful requests create an entry on the Jobs page, where results and history can be viewed.</p>";
            };

            // The hash helper emits NewHashGenerated whenever a new key is available
            if (scope.removeNewHashGenerated) {
                scope.removeNewHashGenerated();
            }
            scope.removeNewHashGenerated = scope.$on('NewHashGenerated', function() {
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
    }

CallbackHelpInit.$inject =
    [   '$q', '$location', 'GetBasePath', 'Rest', 'JobTemplateForm', 'GenerateForm',
        '$stateParams', 'ProcessErrors', 'ParseVariableString',
        'Empty', 'Wait', 'MultiCredentialService', '$rootScope'
    ];
