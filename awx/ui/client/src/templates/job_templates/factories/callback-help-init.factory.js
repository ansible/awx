export default
    function CallbackHelpInit($q, $location, GetBasePath, Rest, JobTemplateForm, GenerateForm, $stateParams, ProcessErrors,
             ParseVariableString, Empty, Wait, MultiCredentialService, $rootScope) {
        return function(params) {
            var scope = params.scope,
            defaultUrl = GetBasePath('job_templates'),
            // generator = GenerateForm,
            form = JobTemplateForm(),
            // loadingFinishedCount = 0,
            // base = $location.path().replace(/^\//, '').split('/')[0],
            master = {},
            id = $stateParams.job_template_id;
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

            // this fills the job template form both on copy of the job template
            // and on edit
            scope.fillJobTemplate  = function(){
                // id = id || $rootScope.copy.id;
                // Retrieve detail record and prepopulate the form
                Rest.setUrl(defaultUrl + id);
                Rest.get()
                .success(function (data) {
                    scope.job_template_obj = data;
                    scope.name = data.name;
                    var fld, i;
                    for (fld in form.fields) {
                        if (fld !== 'variables' && fld !== 'survey' && fld !== 'forks' && data[fld] !== null && data[fld] !== undefined) {
                            if (form.fields[fld].type === 'select') {
                                if (scope[fld + '_options'] && scope[fld + '_options'].length > 0) {
                                    for (i = 0; i < scope[fld + '_options'].length; i++) {
                                        if (data[fld] === scope[fld + '_options'][i].value) {
                                            scope[fld] = scope[fld + '_options'][i];
                                        }
                                    }
                                } else {
                                    scope[fld] = data[fld];
                                }
                            } else {
                                scope[fld] = data[fld];
                                if(!Empty(data.summary_fields.survey)) {
                                    scope.survey_exists = true;
                                }
                            }
                            master[fld] = scope[fld];
                        }
                        if (fld === 'forks') {
                            if (data[fld] !== 0) {
                                scope[fld] = data[fld];
                                master[fld] = scope[fld];
                            }
                        }
                        if (fld === 'variables') {
                            // Parse extra_vars, converting to YAML.
                            scope.variables = ParseVariableString(data.extra_vars);
                            master.variables = scope.variables;
                        }
                        if (form.fields[fld].type === 'lookup' && data.summary_fields[form.fields[fld].sourceModel]) {
                            scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                            master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField];
                        }
                        if (form.fields[fld].type === 'checkbox_group') {
                            for(var j=0; j<form.fields[fld].fields.length; j++) {
                                scope[form.fields[fld].fields[j].name] = data[form.fields[fld].fields[j].name];
                            }
                        }
                    }
                    Wait('stop');
                    scope.url = data.url;

                    scope.survey_enabled = data.survey_enabled;

                    scope.ask_variables_on_launch = (data.ask_variables_on_launch) ? true : false;
                    master.ask_variables_on_launch = scope.ask_variables_on_launch;

                    scope.ask_verbosity_on_launch = (data.ask_verbosity_on_launch) ? true : false;
                    master.ask_verbosity_on_launch = scope.ask_verbosity_on_launch;

                    scope.ask_limit_on_launch = (data.ask_limit_on_launch) ? true : false;
                    master.ask_limit_on_launch = scope.ask_limit_on_launch;

                    scope.ask_tags_on_launch = (data.ask_tags_on_launch) ? true : false;
                    master.ask_tags_on_launch = scope.ask_tags_on_launch;

                    scope.ask_skip_tags_on_launch = (data.ask_skip_tags_on_launch) ? true : false;
                    master.ask_skip_tags_on_launch = scope.ask_skip_tags_on_launch;

                    scope.ask_diff_mode_on_launch = (data.ask_diff_mode_on_launch) ? true : false;
                    master.ask_diff_mode_on_launch = scope.ask_diff_mode_on_launch;

                    scope.job_tag_options = (data.job_tags) ? data.job_tags.split(',')
                        .map((i) => ({name: i, label: i, value: i})) : [];
                    scope.job_tags = scope.job_tag_options;
                    master.job_tags = scope.job_tags;

                    scope.skip_tag_options = (data.skip_tags) ? data.skip_tags.split(',')
                        .map((i) => ({name: i, label: i, value: i})) : [];
                    scope.skip_tags = scope.skip_tag_options;
                    master.skip_tags = scope.skip_tags;

                    scope.ask_job_type_on_launch = (data.ask_job_type_on_launch) ? true : false;
                    master.ask_job_type_on_launch = scope.ask_job_type_on_launch;

                    scope.ask_inventory_on_launch = (data.ask_inventory_on_launch) ? true : false;
                    master.ask_inventory_on_launch = scope.ask_inventory_on_launch;

                    scope.ask_credential_on_launch = (data.ask_credential_on_launch) ? true : false;
                    master.ask_credential_on_launch = scope.ask_credential_on_launch;

                    if (data.host_config_key) {
                        scope.example_config_key = data.host_config_key;
                    }
                    scope.example_template_id = id;
                    scope.setCallbackHelp();

                    scope.callback_url = scope.callback_server_path + ((data.related.callback) ? data.related.callback :
                    GetBasePath('job_templates') + id + '/callback/');
                    master.callback_url = scope.callback_url;

                    scope.can_edit = data.summary_fields.user_capabilities.edit;

                    if(scope.job_template_obj.summary_fields.user_capabilities.edit) {
                        MultiCredentialService.loadCredentials(data)
                            .then(([selectedCredentials, credTypes, credTypeOptions,
                                credTags]) => {
                                    scope.selectedCredentials = selectedCredentials;
                                    scope.credential_types = credTypes;
                                    scope.credentialTypeOptions = credTypeOptions;
                                    scope.credentialsToPost = credTags;console.log(credTags);
                                    scope.$emit('jobTemplateLoaded', master);
                                });
                    }
                    else {

                        if (data.summary_fields.credential) {
                            scope.selectedCredentials.machine = data.summary_fields.credential;
                        }

                        if (data.summary_fields.vault_credential) {
                            scope.selectedCredentials.vault = data.summary_fields.vault_credential;
                        }

                        // Extra credentials are not included in summary_fields so we have to go
                        // out and get them ourselves.

                        let defers = [],
                            typesArray = [],
                            credTypeOptions;

                        Rest.setUrl(data.related.extra_credentials);
                        defers.push(Rest.get()
                            .then((data) => {
                                scope.selectedCredentials.extra = data.data.results;
                            })
                            .catch(({data, status}) => {
                                ProcessErrors(null, data, status, null,
                                    {
                                        hdr: 'Error!',
                                        msg: 'Failed to get extra credentials. ' +
                                        'Get returned status: ' +
                                        status
                                    });
                            }));

                        defers.push(MultiCredentialService.getCredentialTypes()
                            .then(({credential_types, credentialTypeOptions}) => {
                                typesArray = Object.keys(credential_types).map(key => credential_types[key]);
                                credTypeOptions = credentialTypeOptions;
                            })
                        );


                        return $q.all(defers).then(() => {
                            let machineAndVaultCreds = [],
                                extraCreds = [];

                            if(scope.selectedCredentials.machine) {
                                machineAndVaultCreds.push(scope.selectedCredentials.machine);
                            }
                            if(scope.selectedCredentials.vault) {
                                machineAndVaultCreds.push(scope.selectedCredentials.vault);
                            }

                            machineAndVaultCreds.map(cred => ({
                                name: cred.name,
                                id: cred.id,
                                postType: cred.postType,
                                kind: typesArray
                                    .filter(type => {
                                        return cred.kind === type.kind || parseInt(cred.credential_type) === type.value;
                                    })[0].name + ":"
                            }));

                            extraCreds = extraCreds.concat(scope.selectedCredentials.extra).map(cred => ({
                                name: cred.name,
                                id: cred.id,
                                postType: cred.postType,
                                kind: credTypeOptions
                                    .filter(type => {
                                        return parseInt(cred.credential_type) === type.value;
                                    })[0].name + ":"
                            }));

                            scope.credentialsToPost = machineAndVaultCreds.concat(extraCreds);

                            scope.$emit('jobTemplateLoaded', master);
                        });

                    }
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to retrieve job template: ' + $stateParams.id + '. GET status: ' + status
                    });
                });
            };
        };
    }

CallbackHelpInit.$inject =
    [   '$q', '$location', 'GetBasePath', 'Rest', 'JobTemplateForm', 'GenerateForm',
        '$stateParams', 'ProcessErrors', 'ParseVariableString',
        'Empty', 'Wait', 'MultiCredentialService', '$rootScope'
    ];
