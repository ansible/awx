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
        i18n
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
            {label: i18n._('Misc. System'), value: 'misc'},
            {label: i18n._('Activity Stream'), value: 'activity_stream'},
            {label: i18n._('Logging'), value: 'logging'},
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
                awPopOver: $scope.$parent.configDataResolve[key].help_text,
                label: $scope.$parent.configDataResolve[key].label,
                name: key,
                toggleSource: key,
                dataPlacement: 'top',
                placeholder: ConfigurationUtils.formatPlaceholder($scope.$parent.configDataResolve[key].placeholder, key) || null,
                dataTitle: $scope.$parent.configDataResolve[key].label,
                required: $scope.$parent.configDataResolve[key].required,
                ngDisabled: $rootScope.user_is_system_auditor
            });
        }

        $scope.$parent.parseType = 'json';

        _.each(systemForms, function(form) {
            generator.inject(form.formDef, {
                id: form.id,
                mode: 'edit',
                scope: $scope.$parent,
                related: true
            });
        });

        var dropdownRendered = false;

        $scope.$on('populated', function() {

            var opts = [];
            if($scope.$parent.LOG_AGGREGATOR_TYPE !== null) {
                _.each(ConfigurationUtils.listToArray($scope.$parent.LOG_AGGREGATOR_TYPE), function(type) {
                    opts.push({
                        id: type,
                        text: type
                    });
                });
            }

            if(!dropdownRendered) {
                dropdownRendered = true;
                CreateSelect2({
                    element: '#configuration_logging_template_LOG_AGGREGATOR_TYPE',
                    multiple: true,
                    placeholder: i18n._('Select types'),
                    opts: opts
                });
            }

        });

        // Fix for bug where adding selected opts causes form to be $dirty and triggering modal
        // TODO Find better solution for this bug
        $timeout(function(){
            $scope.$parent.configuration_logging_template_form.$setPristine();
        }, 1000);

        angular.extend(systemVm, {
            activeForm: activeForm,
            activeSystemForm: activeSystemForm,
            dropdownOptions: dropdownOptions,
            dropdownValue: dropdownValue,
            systemForms: systemForms
        });
    }
];
