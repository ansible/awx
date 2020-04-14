/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$rootScope', '$scope', '$stateParams',
    'systemActivityStreamForm',
    'systemLoggingForm',
    'systemMiscForm',
    'SettingsUtils',
    'CreateSelect2',
    'GenerateForm',
    'i18n',
    'Rest',
    'ProcessErrors',
    'ngToast',
    '$filter',
    function (
        $rootScope, $scope, $stateParams,
        systemActivityStreamForm,
        systemLoggingForm,
        systemMiscForm,
        SettingsUtils,
        CreateSelect2,
        GenerateForm,
        i18n,
        Rest,
        ProcessErrors,
        ngToast,
        $filter
    ) {
        var systemVm = this;

        var generator = GenerateForm;
        var formTracker = $scope.$parent.vm.formTracker;
        var activeSystemForm = 'misc';

        if ($stateParams.form === 'system') {
            formTracker.setCurrentSystem(activeSystemForm);
        }

        var activeForm = function (tab) {
            if (!_.get($scope.$parent, [formTracker.currentFormName(), '$dirty'])) {
                systemVm.activeSystemForm = tab;
                formTracker.setCurrentSystem(systemVm.activeSystemForm);
            } else {
                var msg = i18n._('You have unsaved changes. Would you like to proceed <strong>without</strong> saving?');
                var title = i18n._('Warning: Unsaved Changes');
                var buttons = [{
                    label: i18n._('Discard changes'),
                    "class": "btn Form-cancelButton",
                    "id": "formmodal-cancel-button",
                    onClick: function () {
                        $scope.$parent.vm.populateFromApi();
                        $scope.$parent[formTracker.currentFormName()].$setPristine();
                        systemVm.activeSystemForm = tab;
                        formTracker.setCurrentSystem(systemVm.activeSystemForm);
                        $('#FormModal-dialog').dialog('close');
                    }
                }, {
                    label: i18n._('Save changes'),
                    onClick: function () {
                        $scope.$parent.vm.formSave()
                            .then(function () {
                                $scope.$parent[formTracker.currentFormName()].$setPristine();
                                $scope.$parent.vm.populateFromApi();
                                systemVm.activeSystemForm = tab;
                                formTracker.setCurrentSystem(systemVm.activeSystemForm);
                                $('#FormModal-dialog').dialog('close');
                            });
                    },
                    "class": "btn btn-primary",
                    "id": "formmodal-save-button"
                }];
                $scope.$parent.vm.triggerModal(msg, title, buttons);
            }
            formTracker.setCurrentSystem(systemVm.activeSystemForm);
        };

        var dropdownOptions = [
            { label: i18n._('Misc. System'), value: 'misc' },
            { label: i18n._('Activity Stream'), value: 'activity_stream' },
            { label: i18n._('Logging'), value: 'logging' },
        ];

        var systemForms = [{
            formDef: systemLoggingForm,
            id: 'system-logging-form'
        }, {
            formDef: systemActivityStreamForm,
            id: 'system-activity-stream-form'
        }, {
            formDef: systemMiscForm,
            id: 'system-misc-form'
        }];

        var forms = _.map(systemForms, 'formDef');
        _.each(forms, function (form) {
            var keys = _.keys(form.fields);
            _.each(keys, function (key) {
                if ($scope.configDataResolve[key].type === 'choice') {
                    // Create options for dropdowns
                    var optionsGroup = key + '_options';
                    $scope.$parent.$parent[optionsGroup] = [];
                    _.each($scope.configDataResolve[key].choices, function (choice) {
                        $scope.$parent.$parent[optionsGroup].push({
                            name: choice[0],
                            label: choice[1],
                            value: choice[0]
                        });
                    });
                }
                addFieldInfo(form, key);
            });
            // Disable the save button for system auditors
            form.buttons.save.disabled = $rootScope.user_is_system_auditor;
        });

        function addFieldInfo(form, key) {
            _.extend(form.fields[key], {
                awPopOver: ($scope.configDataResolve[key].defined_in_file) ?
                    null : $scope.configDataResolve[key].help_text,
                label: $scope.configDataResolve[key].label,
                name: key,
                toggleSource: key,
                dataPlacement: 'top',
                placeholder: SettingsUtils.formatPlaceholder($scope.configDataResolve[key].placeholder, key) || null,
                dataTitle: $scope.configDataResolve[key].label,
                required: $scope.configDataResolve[key].required,
                ngDisabled: $rootScope.user_is_system_auditor,
                disabled: $scope.configDataResolve[key].disabled || null,
                readonly: $scope.configDataResolve[key].readonly || null,
                definedInFile: $scope.configDataResolve[key].defined_in_file || null
            });
        }

        $scope.$parent.$parent.parseType = 'json';

        _.each(systemForms, function (form) {
            generator.inject(form.formDef, {
                id: form.id,
                mode: 'edit',
                scope: $scope.$parent.$parent,
                related: true,
                noPanel: true
            });
        });

        var dropdownRendered = false;

        $scope.$on('populated', function () {
            populateLogAggregator(false);
        });

        $scope.$on('LOG_AGGREGATOR_TYPE_populated', function (e, data, flag) {
            populateLogAggregator(flag);
        });

        $scope.$on('LOG_AGGREGATOR_PROTOCOL_populated', function (e, data, flag) {
            populateLogAggregator(flag);
        });

        function populateLogAggregator(flag) {

            if ($scope.$parent.$parent.LOG_AGGREGATOR_TYPE !== null) {
                $scope.$parent.$parent.LOG_AGGREGATOR_TYPE = _.find($scope.$parent.$parent.LOG_AGGREGATOR_TYPE_options, { value: $scope.$parent.$parent.LOG_AGGREGATOR_TYPE });
            }

            if ($scope.$parent.$parent.LOG_AGGREGATOR_PROTOCOL !== null) {
                $scope.$parent.$parent.LOG_AGGREGATOR_PROTOCOL = _.find($scope.$parent.$parent.LOG_AGGREGATOR_PROTOCOL_options, { value: $scope.$parent.$parent.LOG_AGGREGATOR_PROTOCOL });
            }

            if ($scope.$parent.$parent.LOG_AGGREGATOR_LEVEL !== null) {
                $scope.$parent.$parent.LOG_AGGREGATOR_LEVEL = _.find($scope.$parent.$parent.LOG_AGGREGATOR_LEVEL_options, { value: $scope.$parent.$parent.LOG_AGGREGATOR_LEVEL });
            }

            if (flag !== undefined) {
                dropdownRendered = flag;
            }

            if (!dropdownRendered) {
                dropdownRendered = true;
                CreateSelect2({
                    element: '#configuration_logging_template_LOG_AGGREGATOR_TYPE',
                    multiple: false,
                    placeholder: i18n._('Select types'),
                });
                $scope.$parent.$parent.configuration_logging_template_form.LOG_AGGREGATOR_TYPE.$setPristine();
                $scope.$parent.$parent.configuration_logging_template_form.LOG_AGGREGATOR_PROTOCOL.$setPristine();
                $scope.$parent.$parent.configuration_logging_template_form.LOG_AGGREGATOR_LEVEL.$setPristine();
            }
        }

        $scope.$watchGroup(['configuration_logging_template_form.$pending', 'configuration_logging_template_form.$dirty', '!logAggregatorEnabled'], (vals) => {
            if (vals.some(val => val === true)) {
                $scope.$parent.vm.disableTestButton = true;
                $scope.$parent.vm.testTooltip = i18n._('Save and enable log aggregation before testing the log aggregator.');
            } else {
                $scope.$parent.vm.disableTestButton = false;
                $scope.$parent.vm.testTooltip = i18n._('Send a test log message to the configured log aggregator.');
            }
        });

        $scope.$parent.vm.testLogging = function () {
            if (!$scope.$parent.vm.disableTestButton) {
                $scope.$parent.vm.disableTestButton = true;
                Rest.setUrl("/api/v2/settings/logging/test/");
                Rest.post({})
                    .then(() => {
                        $scope.$parent.vm.disableTestButton = false;
                        ngToast.success({
                            dismissButton: false,
                            dismissOnTimeout: true,
                            content: `<i class="fa fa-check-circle
                                Toast-successIcon"></i>` +
                                i18n._('Log aggregator test sent successfully.')
                        });
                    })
                    .catch(({ data, status }) => {
                        $scope.$parent.vm.disableTestButton = false;
                        if (status === 400 || status === 500) {
                            ngToast.danger({
                                dismissButton: false,
                                dismissOnTimeout: true,
                                content: '<i class="fa fa-exclamation-triangle Toast-successIcon"></i>' +
                                    i18n._('Log aggregator test failed. <br> Detail: ') + $filter('sanitize')(data.error),
                                additionalClasses: "LogAggregator-failedNotification"
                            });
                        } else {
                            ProcessErrors($scope, data, status, null,
                                {
                                    hdr: i18n._('Error!'),
                                    msg: i18n._('There was an error testing the ' +
                                        'log aggregator. Returned status: ') +
                                        status
                                });
                        }
                    });
            }
        };

        angular.extend(systemVm, {
            activeForm: activeForm,
            activeSystemForm: activeSystemForm,
            dropdownOptions: dropdownOptions,
            systemForms: systemForms
        });
    }
];
