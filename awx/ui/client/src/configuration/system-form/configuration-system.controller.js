/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$rootScope', '$scope', '$state', '$stateParams', '$timeout',
    'AngularCodeMirror',
    'systemActivityStreamForm',
    'systemLoggingForm',
    'systemMiscForm',
    'ConfigurationService',
    'ConfigurationUtils',
    'CreateSelect2',
    'GenerateForm',
    'i18n',
    'Rest',
    'ProcessErrors',
    'ngToast',
    '$filter',
    function(
        $rootScope, $scope, $state, $stateParams, $timeout,
        AngularCodeMirror,
        systemActivityStreamForm,
        systemLoggingForm,
        systemMiscForm,
        ConfigurationService,
        ConfigurationUtils,
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
        var dropdownValue = 'misc';
        var activeSystemForm = 'misc';

        if ($stateParams.currentTab === 'system') {
            formTracker.setCurrentSystem(activeSystemForm);
        }

        var activeForm = function() {
            if(!$scope.$parent[formTracker.currentFormName()].$dirty) {
                systemVm.activeSystemForm = systemVm.dropdownValue;
                formTracker.setCurrentSystem(systemVm.activeSystemForm);
            } else {
                var msg = i18n._('You have unsaved changes. Would you like to proceed <strong>without</strong> saving?');
                var title = i18n._('Warning: Unsaved Changes');
                var buttons = [{
                    label: i18n._('Discard changes'),
                    "class": "btn Form-cancelButton",
                    "id": "formmodal-cancel-button",
                    onClick: function() {
                        $scope.$parent.vm.populateFromApi();
                        $scope.$parent[formTracker.currentFormName()].$setPristine();
                        systemVm.activeSystemForm = systemVm.dropdownValue;
                        formTracker.setCurrentSystem(systemVm.activeSystemForm);
                        $('#FormModal-dialog').dialog('close');
                    }
                }, {
                    label: i18n._('Save changes'),
                    onClick: function() {
                        $scope.$parent.vm.formSave()
                        .then(function() {
                            $scope.$parent[formTracker.currentFormName()].$setPristine();
                            $scope.$parent.vm.populateFromApi();
                            systemVm.activeSystemForm = systemVm.dropdownValue;
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
            {label: i18n._('Activity Stream'), value: 'activity_stream'},
            {label: i18n._('Logging'), value: 'logging'},
            {label: i18n._('Misc. System'), value: 'misc'}
        ];

        CreateSelect2({
            element: '#system-configure-dropdown-nav',
            multiple: false,
        });

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

        var forms = _.pluck(systemForms, 'formDef');
        _.each(forms, function(form) {
            var keys = _.keys(form.fields);
            _.each(keys, function(key) {
                if($scope.$parent.configDataResolve[key].type === 'choice') {
                    // Create options for dropdowns
                    var optionsGroup = key + '_options';
                    $scope.$parent[optionsGroup] = [];
                    _.each($scope.$parent.configDataResolve[key].choices, function(choice){
                        $scope.$parent[optionsGroup].push({
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
                awPopOver: ($scope.$parent.configDataResolve[key].defined_in_file) ?
                    null: $scope.$parent.configDataResolve[key].help_text,
                label: $scope.$parent.configDataResolve[key].label,
                name: key,
                toggleSource: key,
                dataPlacement: 'top',
                placeholder: ConfigurationUtils.formatPlaceholder($scope.$parent.configDataResolve[key].placeholder, key) || null,
                dataTitle: $scope.$parent.configDataResolve[key].label,
                required: $scope.$parent.configDataResolve[key].required,
                ngDisabled: $rootScope.user_is_system_auditor,
                disabled: $scope.$parent.configDataResolve[key].disabled || null,
                readonly: $scope.$parent.configDataResolve[key].readonly || null,
                definedInFile: $scope.$parent.configDataResolve[key].defined_in_file || null
            });
        }

        $scope.$parent.parseType = 'json';

        _.each(systemForms, function(form) {
            generator.inject(form.formDef, {
                id: form.id,
                mode: 'edit',
                scope: $scope.$parent,
                related: true,
                noPanel: true
            });
        });

        var dropdownRendered = false;

        $scope.$on('populated', function() {
            populateLogAggregator(false);
        });

        $scope.$on('LOG_AGGREGATOR_TYPE_populated', function(e, data, flag) {
            populateLogAggregator(flag);
        });

        $scope.$on('LOG_AGGREGATOR_PROTOCOL_populated', function(e, data, flag) {
            populateLogAggregator(flag);
        });

        function populateLogAggregator(flag){
            if($scope.$parent.LOG_AGGREGATOR_TYPE !== null) {
                $scope.$parent.LOG_AGGREGATOR_TYPE = _.find($scope.$parent.LOG_AGGREGATOR_TYPE_options, { value: $scope.$parent.LOG_AGGREGATOR_TYPE });
            }

            if($scope.$parent.LOG_AGGREGATOR_PROTOCOL !== null) {
                $scope.$parent.LOG_AGGREGATOR_PROTOCOL = _.find($scope.$parent.LOG_AGGREGATOR_PROTOCOL_options, { value: $scope.$parent.LOG_AGGREGATOR_PROTOCOL });
            }

            if($scope.$parent.LOG_AGGREGATOR_LEVEL !== null) {
                $scope.$parent.LOG_AGGREGATOR_LEVEL = _.find($scope.$parent.LOG_AGGREGATOR_LEVEL_options, { value: $scope.$parent.LOG_AGGREGATOR_LEVEL });
            }

            if(flag !== undefined){
                dropdownRendered = flag;
            }

            if(!dropdownRendered) {
                dropdownRendered = true;
                CreateSelect2({
                    element: '#configuration_logging_template_LOG_AGGREGATOR_TYPE',
                    multiple: false,
                    placeholder: i18n._('Select types'),
                });
                $scope.$parent.configuration_logging_template_form.LOG_AGGREGATOR_TYPE.$setPristine();
                $scope.$parent.configuration_logging_template_form.LOG_AGGREGATOR_PROTOCOL.$setPristine();
                $scope.$parent.configuration_logging_template_form.LOG_AGGREGATOR_LEVEL.$setPristine();
            }
        }

        // Fix for bug where adding selected opts causes form to be $dirty and triggering modal
        // TODO Find better solution for this bug
        $timeout(function(){
            $scope.$parent.configuration_logging_template_form.$setPristine();
        }, 1000);

        $scope.$parent.vm.testLogging = function() {
            Rest.setUrl("/api/v2/settings/logging/test/");
            Rest.post($scope.$parent.vm.getFormPayload())
                .then(() => {
                    ngToast.success({
                        content: `<i class="fa fa-check-circle
                            Toast-successIcon"></i>` +
                                i18n._('Log aggregator test successful.')
                    });
                })
                .catch(({data, status}) => {
                    if (status === 500) {
                        ngToast.danger({
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
        };

        angular.extend(systemVm, {
            activeForm: activeForm,
            activeSystemForm: activeSystemForm,
            dropdownOptions: dropdownOptions,
            dropdownValue: dropdownValue,
            systemForms: systemForms
        });
    }
];
