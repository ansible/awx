/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$scope', '$state', '$stateParams', '$timeout', '$q', 'Alert', 'ClearScope',
    'ConfigurationService', 'ConfigurationUtils', 'CreateDialog', 'CreateSelect2', 'ParseTypeChange', 'ProcessErrors',
    'Wait', 'configDataResolve',
    //Form definitions
    'configurationGithubForm',
    'configurationGithubOrgForm',
    'configurationGithubTeamForm',
    'configurationGoogleForm',
    'configurationLdapForm',
    'configurationRadiusForm',
    'configurationSamlForm',
    'ConfigurationJobsForm',
    'ConfigurationSystemForm',
    'ConfigurationUiForm',
    function(
        $scope, $state, $stateParams, $timeout, $q, Alert, ClearScope,
        ConfigurationService, ConfigurationUtils, CreateDialog, CreateSelect2, ParseTypeChange, ProcessErrors,
        Wait, configDataResolve,
        //Form definitions
        configurationGithubForm,
        configurationGithubOrgForm,
        configurationGithubTeamForm,
        configurationGoogleForm,
        configurationLdapForm,
        configurationRadiusForm,
        configurationSamlForm,
        ConfigurationJobsForm,
        ConfigurationSystemForm,
        ConfigurationUiForm
    ) {
        var vm = this;

        var formDefs = {
            'github': configurationGithubForm,
            'github_org': configurationGithubOrgForm,
            'github_team': configurationGithubTeamForm,
            'google_oauth': configurationGoogleForm,
            'ldap': configurationLdapForm,
            'radius': configurationRadiusForm,
            'saml': configurationSamlForm,
            'jobs': ConfigurationJobsForm,
            'system': ConfigurationSystemForm,
            'ui': ConfigurationUiForm
        };

        var populateFromApi = function() {
            ConfigurationService.getCurrentValues()
                .then(function(data) {
                    var currentKeys = _.keys(data);
                    _.each(currentKeys, function(key) {
                        if (data[key] !== null && typeof data[key] === 'object') {
                            if (Array.isArray(data[key])) {
                                //handle arrays
                                $scope[key] = ConfigurationUtils.arrayToList(data[key], key);
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
        };

        populateFromApi();

        var formTracker = {
            lastForm: '',
            currentForm: '',
            currentAuth: '',
            setCurrent: function(form) {
                this.lastForm = this.currentForm;
                this.currentForm = form;
            },
            setCurrentAuth: function(form) {
                this.currentAuth = form;
                this.setCurrent(this.currentAuth);
            },
            getCurrent: function() {
                return this.currentForm;
            },
            currentFormName: function() {
                return 'configuration_' + this.currentForm + '_template_form';
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
                    var msg = 'You have unsaved changes. Would you like to proceed <strong>without</strong> saving?';
                    var title = 'Warning: Unsaved Changes';
                    var buttons = [{
                        label: "Discard changes",
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
                        label: "Save changes",
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
            if (setForm === 'auth') {
                // Default to 'github' on first load
                if (formTracker.currentAuth === '') {
                    formTracker.setCurrentAuth('github');
                } else {
                    // If returning to auth tab reset current form to previously viewed
                    formTracker.setCurrentAuth(formTracker.currentAuth);
                }
            } else {
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
                var msg = 'You have unsaved changes. Would you like to proceed <strong>without</strong> saving?';
                var title = 'Warning: Unsaved Changes';
                var buttons = [{
                    label: "Discard changes",
                    "class": "btn Form-cancelButton",
                    "id": "formmodal-cancel-button",
                    onClick: function() {
                        $('#FormModal-dialog').dialog('close');
                        $state.go('setup');
                    }
                }, {
                    label: "Save changes",
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


        $scope.resetValue = function(key) {
            Wait('start');
            var payload = {};
            payload[key] = $scope.configDataResolve[key].default;

            ConfigurationService.patchConfiguration(payload)
                .then(function() {
                    $scope[key] = $scope.configDataResolve[key].default;
                })
                .catch(function(error) {
                    ProcessErrors($scope, error, status, formDefs[formTracker.getCurrent()],
                        {
                            hdr: 'Error!',
                            msg: 'There was an error resetting value. Returned status: ' + error.detail
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
        var formSave = function() {
            var saveDeferred = $q.defer();
            var keys = _.keys(formDefs[formTracker.getCurrent()].fields);
            var payload = {};
            clearApiErrors();
            _.each(keys, function(key) {
                if($scope.configDataResolve[key].type === 'choice' || multiselectDropdowns.indexOf(key) !== -1) {
                    //Parse dropdowns and dropdowns labeled as lists
                    if($scope[key] === null) {
                        payload[key] = null;
                    } else if($scope[key][0] && $scope[key][0].value !== undefined) {
                        payload[key] = _.map($scope[key], 'value').join(',');
                    } else {
                        payload[key] = $scope[key].value;
                    }
                } else if($scope.configDataResolve[key].type === 'list' && $scope[key] !== null) {
                    // Parse lists
                    payload[key] = ConfigurationUtils.listToArray($scope[key], key);
                }
                else if($scope.configDataResolve[key].type === 'nested object') {
                    if($scope[key] === '') {
                        payload[key] = {};
                    } else {
                        payload[key] = JSON.parse($scope[key]);
                    }
                }
                else {
                    // Everything else
                    payload[key] = $scope[key];
                }
            });

            Wait('start');
            ConfigurationService.patchConfiguration(payload)
                .then(function(data) {
                    saveDeferred.resolve(data);
                    $scope[formTracker.currentFormName()].$setPristine();
                })
                .catch(function(error, status) {
                    ProcessErrors($scope, error, status, formDefs[formTracker.getCurrent()],
                        {
                            hdr: 'Error!',
                            msg: 'Failed to save settings. Returned status: ' + status
                        });
                    saveDeferred.reject(error);
                })
                .finally(function() {
                    Wait('stop');
                });

            return saveDeferred.promise;
        };

        $scope.toggleForm = function(key) {
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
                            hdr: 'Error!',
                            msg: 'Failed to save toggle settings. Returned status: ' + error.detail
                        });
                })
                .finally(function() {
                    Wait('stop');
                });
        };

        var resetAll = function() {
            Wait('start');
            ConfigurationService.resetAll()
                .then(function() {
                    populateFromApi();
                    $scope[formTracker.currentFormName()].$setPristine();
                })
                .catch(function(error) {
                    ProcessErrors($scope, error, status, formDefs[formTracker.getCurrent()],
                        {
                            hdr: 'Error!',
                            msg: 'There was an error resetting values. Returned status: ' + error.detail
                        });
                })
                .finally(function() {
                    Wait('stop');
                });
        };

        var resetAllConfirm = function() {
            var buttons = [{
                label: "Cancel",
                "class": "btn btn-default",
                "id": "formmodal-cancel-button",
                onClick: function() {
                    $('#FormModal-dialog').dialog('close');
                }
            }, {
                label: "Confirm Reset",
                onClick: function() {
                    resetAll();
                    $('#FormModal-dialog').dialog('close');
                },
                "class": "btn btn-primary",
                "id": "formmodal-reset-button"
            }];
            var msg = 'This will reset all configuration values to their factory defaults. Are you sure you want to proceed?';
            var title = 'Confirm factory reset';
            triggerModal(msg, title, buttons);
        };

        angular.extend(vm, {
            activeTab: activeTab,
            activeTabCheck: activeTabCheck,
            currentForm: currentForm,
            formCancel: formCancel,
            formTracker: formTracker,
            formSave: formSave,
            populateFromApi: populateFromApi,
            resetAllConfirm: resetAllConfirm,
            triggerModal: triggerModal
        });
    }
];
