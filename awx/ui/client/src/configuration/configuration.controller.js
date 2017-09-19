/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$scope', '$rootScope', '$state', '$stateParams', '$timeout', '$q', 'Alert',
    'ConfigurationService', 'ConfigurationUtils', 'CreateDialog', 'CreateSelect2', 'i18n', 'ParseTypeChange', 'ProcessErrors', 'Store',
    'Wait', 'configDataResolve', 'ToJSON', 'ConfigService',
    //Form definitions
    'configurationAzureForm',
    'configurationGithubForm',
    'configurationGithubOrgForm',
    'configurationGithubTeamForm',
    'configurationGoogleForm',
    'configurationLdapForm',
    'configurationRadiusForm',
    'configurationTacacsForm',
    'configurationSamlForm',
    'systemActivityStreamForm',
    'systemLoggingForm',
    'systemMiscForm',
    'ConfigurationJobsForm',
    'ConfigurationUiForm',
    function(
        $scope, $rootScope, $state, $stateParams, $timeout, $q, Alert,
        ConfigurationService, ConfigurationUtils, CreateDialog, CreateSelect2, i18n, ParseTypeChange, ProcessErrors, Store,
        Wait, configDataResolve, ToJSON, ConfigService,
        //Form definitions
        configurationAzureForm,
        configurationGithubForm,
        configurationGithubOrgForm,
        configurationGithubTeamForm,
        configurationGoogleForm,
        configurationLdapForm,
        configurationRadiusForm,
        configurationTacacsForm,
        configurationSamlForm,
        systemActivityStreamForm,
        systemLoggingForm,
        systemMiscForm,
        ConfigurationJobsForm,
        ConfigurationUiForm
    ) {
        var vm = this;

        var formDefs = {
            'azure': configurationAzureForm,
            'github': configurationGithubForm,
            'github_org': configurationGithubOrgForm,
            'github_team': configurationGithubTeamForm,
            'google_oauth': configurationGoogleForm,
            'ldap': configurationLdapForm,
            'radius': configurationRadiusForm,
            'tacacs': configurationTacacsForm,
            'saml': configurationSamlForm,
            'activity_stream': systemActivityStreamForm,
            'logging': systemLoggingForm,
            'misc': systemMiscForm,
            'jobs': ConfigurationJobsForm,
            'ui': ConfigurationUiForm
        };

        var populateFromApi = function() {
            ConfigurationService.getCurrentValues()
                .then(function(data) {
                    var currentKeys = _.keys(data);
                    $scope.requiredLogValues = {};
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
                                if(key === "AD_HOC_COMMANDS"){
                                    $scope[key] = data[key];
                                } else if (key === "AUTH_LDAP_USER_SEARCH" || key === "AUTH_LDAP_GROUP_SEARCH") {
                                    $scope[key] = JSON.stringify(data[key]);
                                } else {
                                    $scope[key] = ConfigurationUtils.arrayToList(data[key], key);
                                }

                            } else {
                                //handle nested objects
                                if(ConfigurationUtils.isEmpty(data[key])) {
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
                ConfigService.getConfig()
                    .then(function(data) {
                        $scope.ldap_auth = data.license_info.features.ldap;
                        $scope.enterprise_auth = data.license_info.features.enterprise_auth;
                    })
                    .catch(function(data, status) {
                        ProcessErrors($scope, data, status, null,
                            {
                                hdr: i18n._('Error'),
                                msg: i18n._('There was an error getting config values: ') + status
                            }
                        );
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
            }
        };

        // Default to auth form and tab
        if ($stateParams.currentTab === '') {
            $state.go('configuration', {
                currentTab: 'auth'
            }, {
                location: true,
                inherit: false,
                notify: false,
                reload: false
            });
        }

        var currentForm = '';
        var currentTab = function() {
            if ($stateParams.currentTab === '' || $stateParams.currentTab === 'auth') {
                return 'auth';
            } else if ($stateParams.currentTab !== '' && $stateParams.currentTab !== 'auth') {
                formTracker.setCurrent($stateParams.currentTab);
                return $stateParams.currentTab;
            }
        };
        var activeTab = currentTab();

        $scope.configDataResolve = configDataResolve;

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

        function activeTabCheck(setForm) {
            if(!$scope[formTracker.currentFormName()].$dirty) {
                active(setForm);
            } else {
                    var msg = i18n._('You have unsaved changes. Would you like to proceed <strong>without</strong> saving?');
                    var title = i18n._('Warning: Unsaved Changes');
                    var buttons = [{
                        label: i18n._("Discard changes"),
                        "class": "btn Form-cancelButton",
                        "id": "formmodal-cancel-button",
                        onClick: function() {
                            clearApiErrors();
                            populateFromApi();
                            $scope[formTracker.currentFormName()].$setPristine();
                            $('#FormModal-dialog').dialog('close');
                            active(setForm);
                        }
                    }, {
                        label: i18n._("Save changes"),
                        onClick: function() {
                            vm.formSave();
                            $scope[formTracker.currentFormName()].$setPristine();
                            $('#FormModal-dialog').dialog('close');
                            active(setForm);
                        },
                        "class": "btn btn-primary",
                        "id": "formmodal-save-button"
                    }];
                    triggerModal(msg, title, buttons);
            }
        }

        function active(setForm) {
            // Authentication and System's sub-module dropdowns handled first:
            if (setForm === 'auth') {
                // Default to 'azure' on first load
                if (formTracker.currentAuth === '') {
                    formTracker.setCurrentAuth('azure');
                } else {
                    // If returning to auth tab reset current form to previously viewed
                    formTracker.setCurrentAuth(formTracker.currentAuth);
                }
            } else if (setForm === 'system') {
                if (formTracker.currentSystem === '') {
                    formTracker.setCurrentSystem('misc');
                } else {
                    // If returning to system tab reset current form to previously viewed
                    formTracker.setCurrentSystem(formTracker.currentSystem);
                }
            }
            else {
                formTracker.setCurrent(setForm);
            }
            vm.activeTab = setForm;
            $state.go('configuration', {
                currentTab: setForm
            }, {
                location: true,
                inherit: false,
                notify: false,
                reload: false
            });
        }

        var formCancel = function() {
            if ($scope[formTracker.currentFormName()].$dirty === true) {
                var msg = i18n._('You have unsaved changes. Would you like to proceed <strong>without</strong> saving?');
                var title = i18n._('Warning: Unsaved Changes');
                var buttons = [{
                    label: i18n._("Discard changes"),
                    "class": "btn Form-cancelButton",
                    "id": "formmodal-cancel-button",
                    onClick: function() {
                        $('#FormModal-dialog').dialog('close');
                        $state.go('setup');
                    }
                }, {
                    label: i18n._("Save changes"),
                    onClick: function() {
                        $scope.formSave();
                        $('#FormModal-dialog').dialog('close');
                        $state.go('setup');
                    },
                    "class": "btn btn-primary",
                    "id": "formmodal-save-button"
                }];
                triggerModal(msg, title, buttons);
            } else {
                $state.go('setup');
            }
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
            payload[key] = $scope.configDataResolve[key].default;

            ConfigurationService.patchConfiguration(payload)
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
                        if (key === "AUTH_LDAP_USER_SEARCH" || key === "AUTH_LDAP_GROUP_SEARCH") {
                            $scope[key] = '[]';
                        } else {
                            $scope[key] = '{}';
                        }
                        $scope.$broadcast('codeMirror_populated', key);
                    }
                    loginUpdate();
                })
                .catch(function(error) {
                    ProcessErrors($scope, error, status, formDefs[formTracker.getCurrent()],
                        {
                            hdr: i18n._('Error!'),
                            msg: i18n._('There was an error resetting value. Returned status: ') + error.detail
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

            _.each(keys, function(key) {
                if($scope.configDataResolve[key].type === 'choice' || multiselectDropdowns.indexOf(key) !== -1) {
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
                    payload[key] = ConfigurationUtils.listToArray($scope[key], key);
                }
                else if($scope.configDataResolve[key].type === 'nested object') {
                    if($scope[key] === '') {
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
                        ($scope.LOG_AGGREGATOR_PROTOCOL === 'https' ||
                            $scope.LOG_AGGREGATOR_PROTOCOL === 'tcp')) {
                                payload[key] = $scope[key];
                    }
                }
            });

            return payload;
        };

        var formSave = function() {
            var saveDeferred = $q.defer();
            clearApiErrors();
            Wait('start');
            ConfigurationService.patchConfiguration(getFormPayload())
                .then(function(data) {
                    loginUpdate();

                    $scope.requiredLogValues.LOG_AGGREGATOR_HOST = $scope.LOG_AGGREGATOR_HOST;
                    $scope.requiredLogValues.LOG_AGGREGATOR_TYPE = $scope.LOG_AGGREGATOR_TYPE;

                    saveDeferred.resolve(data);
                    $scope[formTracker.currentFormName()].$setPristine();
                })
                .catch(function(error, status) {
                    ProcessErrors($scope, error, status, formDefs[formTracker.getCurrent()],
                        {
                            hdr: i18n._('Error!'),
                            msg: i18n._('Failed to save settings. Returned status: ') + status
                        });
                    saveDeferred.reject(error);
                })
                .finally(function() {
                    Wait('stop');
                });

            return saveDeferred.promise;
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
            ConfigurationService.patchConfiguration(payload)
                .then(function() {
                    //TODO consider updating form values with returned data here
                })
                .catch(function(error, status) {
                    //Change back on unsuccessful update
                    $scope[key] = !$scope[key];
                    ProcessErrors($scope, error, status, formDefs[formTracker.getCurrent()],
                        {
                            hdr: i18n._('Error!'),
                            msg: i18n._('Failed to save toggle settings. Returned status: ') + error.detail
                        });
                })
                .finally(function() {
                    Wait('stop');
                });
        };

        var resetAll = function() {
            var keys = _.keys(formDefs[formTracker.getCurrent()].fields);
            var payload = {};
            clearApiErrors();
            _.each(keys, function(key) {
                payload[key] = $scope.configDataResolve[key].default;
            });

            Wait('start');
            ConfigurationService.patchConfiguration(payload)
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
                .catch(function(error) {
                    ProcessErrors($scope, error, status, formDefs[formTracker.getCurrent()],
                        {
                            hdr: i18n._('Error!'),
                            msg: i18n._('There was an error resetting values. Returned status: ') + error.detail
                        });
                })
                .finally(function() {
                    Wait('stop');
                });
        };

        var resetAllConfirm = function() {
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

        var show_auditor_bar;
        if($rootScope.user_is_system_auditor && Store('show_auditor_bar') !== false) {
            show_auditor_bar = true;
        } else {
            show_auditor_bar = false;
        }

        var updateMessageBarPrefs = function() {
            vm.show_auditor_bar = false;
            Store('show_auditor_bar', vm.show_auditor_bar);
        };

        var closeMessageBar = function() {
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

        angular.extend(vm, {
            activeTab: activeTab,
            activeTabCheck: activeTabCheck,
            closeMessageBar: closeMessageBar,
            currentForm: currentForm,
            formCancel: formCancel,
            formTracker: formTracker,
            formSave: formSave,
            getFormPayload: getFormPayload,
            populateFromApi: populateFromApi,
            resetAllConfirm: resetAllConfirm,
            show_auditor_bar: show_auditor_bar,
            triggerModal: triggerModal,
        });
    }
];
