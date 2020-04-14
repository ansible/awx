import defaultStrings from '~assets/default.strings.json';

export default [
    '$scope', '$rootScope', '$state', '$stateParams', '$q',
    'SettingsService', 'SettingsUtils', 'CreateDialog', 'i18n', 'ProcessErrors', 'Store',
    'Wait', 'configDataResolve', 'ToJSON', 'ConfigService',
    //Form definitions
    'configurationAzureForm',
    'configurationGithubForm',
    'configurationGithubOrgForm',
    'configurationGithubTeamForm',
    'configurationGoogleForm',
    'configurationLdapForm',
    'configurationLdap1Form',
    'configurationLdap2Form',
    'configurationLdap3Form',
    'configurationLdap4Form',
    'configurationLdap5Form',
    'configurationRadiusForm',
    'configurationTacacsForm',
    'configurationSamlForm',
    'systemActivityStreamForm',
    'systemLoggingForm',
    'systemMiscForm',
    'ConfigurationJobsForm',
    'ConfigurationUiForm',
    'ngToast',
    function(
        $scope, $rootScope, $state, $stateParams, $q,
        SettingsService, SettingsUtils, CreateDialog, i18n, ProcessErrors, Store,
        Wait, configDataResolve, ToJSON, ConfigService,
        //Form definitions
        configurationAzureForm,
        configurationGithubForm,
        configurationGithubOrgForm,
        configurationGithubTeamForm,
        configurationGoogleForm,
        configurationLdapForm,
        configurationLdap1Form,
        configurationLdap2Form,
        configurationLdap3Form,
        configurationLdap4Form,
        configurationLdap5Form,
        configurationRadiusForm,
        configurationTacacsForm,
        configurationSamlForm,
        systemActivityStreamForm,
        systemLoggingForm,
        systemMiscForm,
        ConfigurationJobsForm,
        ConfigurationUiForm,
        ngToast
    ) {
        const vm = this;

        vm.product = defaultStrings.BRAND_NAME;
        vm.activeTab = $stateParams.form;

        const formDefs = {
            'azure': configurationAzureForm,
            'github': configurationGithubForm,
            'github_org': configurationGithubOrgForm,
            'github_team': configurationGithubTeamForm,
            'google_oauth': configurationGoogleForm,
            'ldap': configurationLdapForm,
            'ldap1': configurationLdap1Form,
            'ldap2': configurationLdap2Form,
            'ldap3': configurationLdap3Form,
            'ldap4': configurationLdap4Form,
            'ldap5': configurationLdap5Form,
            'radius': configurationRadiusForm,
            'tacacs': configurationTacacsForm,
            'saml': configurationSamlForm,
            'activity_stream': systemActivityStreamForm,
            'logging': systemLoggingForm,
            'misc': systemMiscForm,
            'jobs': ConfigurationJobsForm,
            'ui': ConfigurationUiForm
        };

        $scope.configDataResolve = configDataResolve;
        $scope.formDefs = formDefs;

        // check if it's auditor, show messageBar
        $scope.show_auditor_bar = false;
        if($rootScope.user_is_system_auditor && Store('show_auditor_bar') !== false) {
            $scope.show_auditor_bar = true;
        } else {
            $scope.show_auditor_bar = false;
        }

        var populateFromApi = function() {
            SettingsService.getCurrentValues()
                .then(function(data) {
                    $scope.logAggregatorEnabled = data.LOG_AGGREGATOR_ENABLED;
                    // these two values need to be unnested from the
                    // OAUTH2_PROVIDER key
                    data.ACCESS_TOKEN_EXPIRE_SECONDS = data
                        .OAUTH2_PROVIDER.ACCESS_TOKEN_EXPIRE_SECONDS;
                    data.REFRESH_TOKEN_EXPIRE_SECONDS = data
                        .OAUTH2_PROVIDER.REFRESH_TOKEN_EXPIRE_SECONDS;
                    data.AUTHORIZATION_CODE_EXPIRE_SECONDS = data
                        .OAUTH2_PROVIDER.AUTHORIZATION_CODE_EXPIRE_SECONDS;
                    var currentKeys = _.keys(data);
                    $scope.requiredLogValues = {};
                    $scope.originalSettings = data;
                    _.each(currentKeys, function(key) {
                        if(key === "LOG_AGGREGATOR_HOST") {
                            $scope.requiredLogValues.LOG_AGGREGATOR_HOST = data[key];
                        }

                        if(key === "LOG_AGGREGATOR_TYPE") {
                            $scope.requiredLogValues.LOG_AGGREGATOR_TYPE = data[key];
                        }

                        if (data[key] !== null && typeof data[key] === 'object') {
                            if (Array.isArray(data[key])) {
                                //handle arrays
                                //having to do this particular check b/c
                                // we want the options w/o a space, and
                                // the ConfigurationUtils.arrayToList()
                                // does a string.split(', ') w/ an extra space
                                // behind the comma.

                                const isLdap = (key.indexOf("AUTH_LDAP") !== -1);
                                const isLdapUserSearch = isLdap && (key.indexOf("USER_SEARCH") !== -1);
                                const isLdapGroupSearch = isLdap && (key.indexOf("GROUP_SEARCH") !== -1);

                                if(key === "AD_HOC_COMMANDS"){
                                    $scope[key] = data[key];
                                } else if (isLdapUserSearch || isLdapGroupSearch) {
                                    $scope[key] = JSON.stringify(data[key]);
                                } else {
                                    $scope[key] = SettingsUtils.arrayToList(data[key], key);
                                }

                            } else {
                                //handle nested objects
                                if(SettingsUtils.isEmpty(data[key])) {
                                    $scope[key] = '{}';
                                } else {
                                    $scope[key] = JSON.stringify(data[key]);
                                }
                            }
                        } else {
                            $scope[key] = data[key];
                        }
                    });
                    $scope.$broadcast('populated', data);
                });
        };

        populateFromApi();

        var formTracker = {
            lastForm: '',
            currentForm: '',
            currentAuth: '',
            currentSystem: '',
            setCurrent: function(form) {
                this.lastForm = this.currentForm;
                this.currentForm = form;
            },
            getCurrent: function() {
                return this.currentForm;
            },
            currentFormName: function() {
                return 'configuration_' + this.currentForm + '_template_form';
            },
            setCurrentAuth: function(form) {
                this.currentAuth = form;
                this.setCurrent(this.currentAuth);
            },
            setCurrentSystem: function(form) {
                this.currentSystem = form;
                this.setCurrent(this.currentSystem);
            },
        };

        var triggerModal = function(msg, title, buttons) {
            if ($scope.removeModalReady) {
                $scope.removeModalReady();
            }
            $scope.removeModalReady = $scope.$on('ModalReady', function() {
                // $('#lookup-save-button').attr('disabled', 'disabled');
                $('#FormModal-dialog').dialog('open');
            });

            $('#FormModal-dialog').html(msg);

            CreateDialog({
                scope: $scope,
                buttons: buttons,
                width: 600,
                height: 200,
                minWidth: 500,
                title: title,
                id: 'FormModal-dialog',
                resizable: false,
                callback: 'ModalReady'
            });
        };

        function loginUpdate() {
            // Updates the logo and app config so that logos and info are properly shown
            // on logout after modifying.
            if($scope.CUSTOM_LOGO) {
                $rootScope.custom_logo = $scope.CUSTOM_LOGO;
                global.$AnsibleConfig.custom_logo = true;
            } else {
                $rootScope.custom_logo = '';
                global.$AnsibleConfig.custom_logo = false;
            }

            if($scope.CUSTOM_LOGIN_INFO) {
                $rootScope.custom_login_info = $scope.CUSTOM_LOGIN_INFO;
                global.$AnsibleConfig.custom_login_info = $scope.CUSTOM_LOGIN_INFO;
            } else {
                $rootScope.custom_login_info = '';
                global.$AnsibleConfig.custom_login_info = false;
            }

            Store('AnsibleConfig', global.$AnsibleConfig);

            $scope.$broadcast('loginUpdated');
        }

        $scope.resetValue = function(key) {
            Wait('start');
            var payload = {};
            if (key === 'ACCESS_TOKEN_EXPIRE_SECONDS'  || key === 'REFRESH_TOKEN_EXPIRE_SECONDS' || key === 'AUTHORIZATION_CODE_EXPIRE_SECONDS') {
                // the reset for these two keys needs to be nested under OAUTH2_PROVIDER
                if (payload.OAUTH2_PROVIDER === undefined) {
                    payload.OAUTH2_PROVIDER = {
                        ACCESS_TOKEN_EXPIRE_SECONDS: $scope.ACCESS_TOKEN_EXPIRE_SECONDS,
                        REFRESH_TOKEN_EXPIRE_SECONDS: $scope.REFRESH_TOKEN_EXPIRE_SECONDS,
                        AUTHORIZATION_CODE_EXPIRE_SECONDS: $scope.AUTHORIZATION_CODE_EXPIRE_SECONDS
                    };
                }
                payload.OAUTH2_PROVIDER[key] = $scope.configDataResolve[key].default;
            } else {
                payload[key] = $scope.configDataResolve[key].default;
            }
            SettingsService.patchConfiguration(payload)
                .then(function() {
                    $scope[key] = $scope.configDataResolve[key].default;

                    if(key === "LOG_AGGREGATOR_HOST" || key === "LOG_AGGREGATOR_TYPE") {
                        $scope.requiredLogValues[key] = $scope.configDataResolve[key].default;
                    }

                    if($scope[key + '_field'].type === "select"){
                        // We need to re-instantiate the Select2 element
                        // after resetting the value. Example:
                        $scope.$broadcast(key+'_populated', null, false);
                        if(key === "AD_HOC_COMMANDS"){
                            $scope.$broadcast(key+'_reverted', null, false);
                        }
                    }
                    else if($scope[key + '_field'].reset === "CUSTOM_LOGO"){
                        $scope.$broadcast(key+'_reverted');
                    }
                    else if($scope[key + '_field'].hasOwnProperty('codeMirror')){
                        const isLdap = (key.indexOf("AUTH_LDAP") !== -1);

                        const isLdapGroupTypeParams = isLdap && (key.indexOf("GROUP_TYPE_PARAMS") !== -1);
                        const isLdapUserSearch = isLdap && (key.indexOf("USER_SEARCH") !== -1);
                        const isLdapGroupSearch = isLdap && (key.indexOf("GROUP_SEARCH") !== -1);

                        if (isLdapGroupTypeParams) {
                            $scope[key] = JSON.stringify($scope.configDataResolve[key].default);
                        } else if (isLdapUserSearch || isLdapGroupSearch) {
                            $scope[key] = '[]';
                        } else {
                            $scope[key] = '{}';
                        }
                        $scope.$broadcast('codeMirror_populated', key);
                    }
                    loginUpdate();
                })
                .catch(function(data) {
                    ProcessErrors($scope, data.error, data.status, formDefs[formTracker.getCurrent()],
                        {
                            hdr: `<i class="fa fa-warning ConfigureTower-errorIcon"></i>
                                <span class="error-color">${ i18n._('Error!')} </span>`,
                            msg: i18n._('There was an error resetting value. Returned status: ') + data.error.detail
                        });

                })
                .finally(function() {
                    Wait('stop');
                });
        };

        function clearApiErrors() {
            var currentForm = formDefs[formTracker.getCurrent()];
            for (var fld in currentForm.fields) {
                if (currentForm.fields[fld].sourceModel) {
                    $scope[currentForm.fields[fld].sourceModel + '_' + currentForm.fields[fld].sourceField + '_api_error'] = '';
                    $('[name="' + currentForm.fields[fld].sourceModel + '_' + currentForm.fields[fld].sourceField + '"]').removeClass('ng-invalid');
                } else if (currentForm.fields[fld].realName) {
                    $scope[currentForm.fields[fld].realName + '_api_error'] = '';
                    $('[name="' + currentForm.fields[fld].realName + '"]').removeClass('ng-invalid');
                } else {
                    $scope[fld + '_api_error'] = '';
                    $('[name="' + fld + '"]').removeClass('ng-invalid');
                }
                if (currentForm.fields[fld].codeMirror) {
                    $('label[for="' + fld + '"] span').removeClass('error-color');
                    $(`#cm-${fld}-container .CodeMirror`).removeClass('error-border');
                }
            }
            if (!$scope.$$phase) {
                $scope.$digest();
            }
        }

        // Some dropdowns are listed as "list" type in the API even though they're a dropdown:
        var multiselectDropdowns = ['AD_HOC_COMMANDS'];

        var getFormPayload = function() {
            var keys = _.keys(formDefs[formTracker.getCurrent()].fields);
            var payload = {};
            const errors = {};

            _.each(keys, function(key) {
                if (key === 'ACCESS_TOKEN_EXPIRE_SECONDS'  || key === 'REFRESH_TOKEN_EXPIRE_SECONDS' || key === 'AUTHORIZATION_CODE_EXPIRE_SECONDS') {
                    // These two values need to be POSTed nested under the OAUTH2_PROVIDER key
                    if (payload.OAUTH2_PROVIDER === undefined) {
                        payload.OAUTH2_PROVIDER = {
                            ACCESS_TOKEN_EXPIRE_SECONDS: $scope.ACCESS_TOKEN_EXPIRE_SECONDS,
                            REFRESH_TOKEN_EXPIRE_SECONDS: $scope.REFRESH_TOKEN_EXPIRE_SECONDS,
                            AUTHORIZATION_CODE_EXPIRE_SECONDS: $scope.AUTHORIZATION_CODE_EXPIRE_SECONDS
                        };
                    }
                    payload.OAUTH2_PROVIDER[key] = $scope[key];
                } else if($scope.configDataResolve[key].type === 'choice' || multiselectDropdowns.indexOf(key) !== -1) {
                    //Parse dropdowns and dropdowns labeled as lists
                    if($scope[key] === null) {
                        payload[key] = null;
                    } else if(!_.isEmpty($scope[`${key}_values`])) {
                        if(multiselectDropdowns.indexOf(key) !== -1) {
                            // Handle AD_HOC_COMMANDS
                            payload[key] = $scope[`${key}_values`];
                        } else {
                            payload[key] = _.map($scope[key], 'value').join(',');
                        }
                    } else {
                        if(multiselectDropdowns.indexOf(key) !== -1) {
                            // Default AD_HOC_COMMANDS to an empty list
                            payload[key] = $scope[key].value || [];
                        } else {
                            if ($scope[key]) {
                                payload[key] = $scope[key].value;
                            }
                        }
                    }
                } else if($scope.configDataResolve[key].type === 'list' && $scope[key] !== null) {
                    // Parse lists
                    try {
                        payload[key] = SettingsUtils.listToArray($scope[key], key); 
                    } catch (error) {
                        errors[key] = error;
                        payload[key] = [];
                    }
                }
                else if($scope.configDataResolve[key].type === 'nested object') {
                    if(!$scope[key]) {
                        payload[key] = {};
                    } else {
                        // payload[key] = JSON.parse($scope[key]);
                        payload[key] = ToJSON($scope.parseType,
                            $scope[key]);
                    }
                }
                else {
                    // Everything else
                    if (key !== 'LOG_AGGREGATOR_TCP_TIMEOUT' ||
                    ($scope.LOG_AGGREGATOR_PROTOCOL &&
                    ($scope.LOG_AGGREGATOR_PROTOCOL.value === 'https' ||
                        $scope.LOG_AGGREGATOR_PROTOCOL.value === 'tcp'))) {
                            payload[key] = $scope[key];
                    }
                }
            });
            return [payload, errors];
        };

        vm.formSave = function() {
            var saveDeferred = $q.defer();
            clearApiErrors();
            Wait('start');

            const [payload, errors] = getFormPayload();
            if (!SettingsUtils.isEmpty(errors)) {
                ProcessErrors($scope, errors, null, formDefs[formTracker.getCurrent()], {});
                return;
            }

            const [payloadCopy] = getFormPayload();
            SettingsService.patchConfiguration(payloadCopy)
                .then(function(data) {
                    loginUpdate();

                    $scope.requiredLogValues.LOG_AGGREGATOR_HOST = $scope.LOG_AGGREGATOR_HOST;
                    $scope.requiredLogValues.LOG_AGGREGATOR_TYPE = $scope.LOG_AGGREGATOR_TYPE;

                    saveDeferred.resolve(data);
                    $scope[formTracker.currentFormName()].$setPristine();
                    ngToast.success({
                        timeout: 2000,
                        dismissButton: false,
                        dismissOnTimeout: true,
                        content: `<i class="fa fa-check-circle
                            Toast-successIcon"></i>` +
                                i18n._('Save Complete')
                    });
                    if(payload.PENDO_TRACKING_STATE && payload.PENDO_TRACKING_STATE !== $scope.originalSettings.PENDO_TRACKING_STATE) {
                        // Refreshing the page will pull in the new config and
                        // properly set pendo up/shut it off depending on the
                        // action
                        location.reload();
                    }
                })
                .catch(function(data) {
                    ProcessErrors($scope, data.data, data.status, formDefs[formTracker.getCurrent()],
                        {
                            hdr: `<i class="fa fa-warning ConfigureTower-errorIcon"></i>
                                <span class="error-color">${ i18n._('Error!')} </span>`,
                            msg: i18n._('Failed to save settings. Returned status: ') + data.status
                        });
                    saveDeferred.reject(data);
                })
                .finally(function() {
                    Wait('stop');
                });

            return saveDeferred.promise;
        };

        vm.formCancel = function() {
            if ($scope[formTracker.currentFormName()].$dirty === true) {
                var msg = i18n._('You have unsaved changes. Would you like to proceed <strong>without</strong> saving?');
                var title = i18n._('Warning: Unsaved Changes');
                var buttons = [{
                    label: i18n._("Discard changes"),
                    "class": "btn Form-cancelButton",
                    "id": "formmodal-cancel-button",
                    onClick: function() {
                        $('#FormModal-dialog').dialog('close');
                        $state.go('settings');
                    }
                }, {
                    label: i18n._("Save changes"),
                    onClick: function() {
                        vm.formSave()
                        .then(function() {
                            $('#FormModal-dialog').dialog('close');
                            $state.go('settings');
                        });
                    },
                    "class": "btn btn-primary",
                    "id": "formmodal-save-button"
                }];
                triggerModal(msg, title, buttons);
            } else {
                $state.go('settings');
            }
        };

        vm.resetAllConfirm = function() {
            var buttons = [{
                label: i18n._("Cancel"),
                "class": "btn btn-default",
                "id": "formmodal-cancel-button",
                onClick: function() {
                    $('#FormModal-dialog').dialog('close');
                }
            }, {
                label: i18n._("Confirm Reset"),
                onClick: function() {
                    resetAll();
                    $('#FormModal-dialog').dialog('close');
                },
                "class": "btn btn-primary",
                "id": "formmodal-reset-button"
            }];
            var msg = i18n._('This will reset all configuration values to their factory defaults. Are you sure you want to proceed?');
            var title = i18n._('Confirm factory reset');
            triggerModal(msg, title, buttons);
        };

        vm.closeMessageBar = function() {
            var msg = 'Are you sure you want to hide the notification bar?';
            var title = 'Warning: Closing notification bar';
            var buttons = [{
                label: "Cancel",
                "class": "btn Form-cancelButton",
                "id": "formmodal-cancel-button",
                onClick: function() {
                    $('#FormModal-dialog').dialog('close');
                }
            }, {
                label: "OK",
                onClick: function() {
                    $('#FormModal-dialog').dialog('close');
                    updateMessageBarPrefs();
                },
                "class": "btn btn-primary",
                "id": "formmodal-save-button"
            }];
            triggerModal(msg, title, buttons);
        };

        vm.getCurrentFormTitle = function() {
            switch($stateParams.form) {
                case 'auth':
                    return 'AUTHENTICATION';
                case 'jobs':
                    return 'JOBS';
                case 'system':
                    return 'SYSTEM';
                case 'ui':
                    return 'USER INTERFACE';
                case 'license':
                    return 'LICENSE';
            }
        };

        $scope.toggleForm = function(key) {
            if($rootScope.user_is_system_auditor) {
                // Block system auditors from making changes
                event.preventDefault();
                return;
            }

            $scope[key] = !$scope[key];
            Wait('start');
            var payload = {};
            payload[key] = $scope[key];
            SettingsService.patchConfiguration(payload)
                .then(function(data) {
                    //TODO consider updating form values with returned data here
                    if (key === 'LOG_AGGREGATOR_ENABLED') {
                        $scope.logAggregatorEnabled = data.LOG_AGGREGATOR_ENABLED;
                    }
                })
                .catch(function(data) {
                    //Change back on unsuccessful update
                    $scope[key] = !$scope[key];
                    ProcessErrors($scope, data.data, data.status, formDefs[formTracker.getCurrent()],
                        {
                            hdr: `<i class="fa fa-warning ConfigureTower-errorIcon"></i>
                                <span class="error-color">${ i18n._('Error!')} </span>`,
                            msg: i18n._('Failed to save toggle settings. Returned status: ') + data.status
                        });
                })
                .finally(function() {
                    Wait('stop');
                });
        };

        function resetAll () {
            var keys = _.keys(formDefs[formTracker.getCurrent()].fields);
            var payload = {};
            clearApiErrors();
            _.each(keys, function(key) {
                if (key === 'ACCESS_TOKEN_EXPIRE_SECONDS'  || key === 'REFRESH_TOKEN_EXPIRE_SECONDS' || key === 'AUTHORIZATION_CODE_EXPIRE_SECONDS') {
                    // the reset for these two keys needs to be nested under OAUTH2_PROVIDER
                    if (payload.OAUTH2_PROVIDER === undefined) {
                        payload.OAUTH2_PROVIDER = {
                            ACCESS_TOKEN_EXPIRE_SECONDS: $scope.ACCESS_TOKEN_EXPIRE_SECONDS,
                            REFRESH_TOKEN_EXPIRE_SECONDS: $scope.REFRESH_TOKEN_EXPIRE_SECONDS,
                            AUTHORIZATION_CODE_EXPIRE_SECONDS: $scope.AUTHORIZATION_CODE_EXPIRE_SECONDS
                        };
                    }
                    payload.OAUTH2_PROVIDER[key] = $scope.configDataResolve[key].default;
                } else {
                    payload[key] = $scope.configDataResolve[key].default;
                }
            });

            Wait('start');
            SettingsService.patchConfiguration(payload)
                .then(function() {
                    populateFromApi();
                    $scope[formTracker.currentFormName()].$setPristine();

                    let keys = _.keys(formDefs[formTracker.getCurrent()].fields);
                    _.each(keys, function(key) {
                        $scope[key] = $scope.configDataResolve[key].default;
                        if($scope[key + '_field'].type === "select"){
                            // We need to re-instantiate the Select2 element
                            // after resetting the value. Example:
                            $scope.$broadcast(key+'_populated', null, false);
                            if(key === "AD_HOC_COMMANDS"){
                                $scope.$broadcast(key+'_reverted', null, false);
                            }
                        }
                        else if($scope[key + '_field'].reset === "CUSTOM_LOGO"){
                            $scope.$broadcast(key+'_reverted');
                        }
                        else if($scope[key + '_field'].hasOwnProperty('codeMirror')){
                            $scope[key] = '{}';
                            $scope.$broadcast('codeMirror_populated', key);
                        }
                    });

                })
                .catch(function(data) {
                    ProcessErrors($scope, data.error, data.status, formDefs[formTracker.getCurrent()],
                        {
                            hdr: `<i class="fa fa-warning ConfigureTower-errorIcon"></i>
                                <span class="error-color">${ i18n._('Error!')} </span>`,
                            msg: i18n._('There was an error resetting values. Returned status: ') + data.error.detail
                        });
                })
                .finally(function() {
                    Wait('stop');
                });
        }

        function updateMessageBarPrefs () {
            $scope.show_auditor_bar = false;
            Store('show_auditor_bar', $scope.show_auditor_bar);
        }

        angular.extend(vm, {
            formTracker: formTracker,
            getFormPayload: getFormPayload,
            populateFromApi: populateFromApi,
            triggerModal: triggerModal,
        });
    }
];
