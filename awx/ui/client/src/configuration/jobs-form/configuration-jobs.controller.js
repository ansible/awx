/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$scope',
    '$rootScope',
    '$state',
    '$timeout',
    'ConfigurationJobsForm',
    'ConfigurationService',
    'ConfigurationUtils',
    'CreateSelect2',
    'GenerateForm',
    'i18n',
    function(
        $scope,
        $rootScope,
        $state,
        $timeout,
        ConfigurationJobsForm,
        ConfigurationService,
        ConfigurationUtils,
        CreateSelect2,
        GenerateForm,
        i18n
    ) {
        var jobsVm = this;
        var generator = GenerateForm;
        var form = ConfigurationJobsForm;
        $scope.$parent.AD_HOC_COMMANDS_options = [];
        _.each($scope.$parent.configDataResolve.AD_HOC_COMMANDS.default, function(command) {
            $scope.$parent.AD_HOC_COMMANDS_options.push({
                name: command,
                label: command,
                value: command
            });
        });

        // Disable the save button for system auditors
        form.buttons.save.disabled = $rootScope.user_is_system_auditor;

        var keys = _.keys(form.fields);
        _.each(keys, function(key) {
            addFieldInfo(form, key);
        });

        function addFieldInfo(form, key) {
            _.extend(form.fields[key], {
                awPopOver: $scope.$parent.configDataResolve[key].help_text,
                label: $scope.$parent.configDataResolve[key].label,
                name: key,
                toggleSource: key,
                dataPlacement: 'top',
                dataTitle: $scope.$parent.configDataResolve[key].label,
                required: $scope.$parent.configDataResolve[key].required,
                ngDisabled: $rootScope.user_is_system_auditor,
                disabled: $scope.$parent.configDataResolve[key].disabled || null,
                readonly: $scope.$parent.configDataResolve[key].readonly || null,
            });
        }

        generator.inject(form, {
            id: 'configure-jobs-form',
            mode: 'edit',
            scope: $scope.$parent,
            related: false
        });

        // Flag to avoid re-rendering and breaking Select2 dropdowns on tab switching
        var dropdownRendered = false;


        function populateAdhocCommand(flag){
            var ad_hoc_commands = $scope.$parent.AD_HOC_COMMANDS.split(',');
            $scope.$parent.AD_HOC_COMMANDS = _.map(ad_hoc_commands, (item) => _.find($scope.$parent.AD_HOC_COMMANDS_options, { value: item }));

            if(flag !== undefined){
                dropdownRendered = flag;
            }

            if(!dropdownRendered) {
                dropdownRendered = true;
                CreateSelect2({
                    element: '#configuration_jobs_template_AD_HOC_COMMANDS',
                    multiple: true,
                    placeholder: i18n._('Select commands')
                });
            }
        }

        $scope.$on('adhoc_populated', function(e, data, flag) {
            populateAdhocCommand(flag);
        });

        $scope.$on('populated', function(e, data, flag) {
            populateAdhocCommand(flag);
        });

        // Fix for bug where adding selected opts causes form to be $dirty and triggering modal
        // TODO Find better solution for this bug
        $timeout(function(){
            $scope.$parent.configuration_jobs_template_form.$setPristine();
        }, 1000);

        angular.extend(jobsVm, {
        });

    }
];
