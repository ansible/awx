/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$scope',
    '$state',
    '$timeout',
    'ConfigurationJobsForm',
    'ConfigurationService',
    'ConfigurationUtils',
    'CreateSelect2',
    'GenerateForm',
    function(
        $scope,
        $state,
        $timeout,
        ConfigurationJobsForm,
        ConfigurationService,
        ConfigurationUtils,
        CreateSelect2,
        GenerateForm
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
                dataTitle: $scope.$parent.configDataResolve[key].label
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

        $scope.$on('populated', function() {
            var opts = [];
            _.each(ConfigurationUtils.listToArray($scope.$parent.AD_HOC_COMMANDS), function(command) {
                opts.push({
                    id: command,
                    text: command
                });
            });

            if(!dropdownRendered) {
                dropdownRendered = true;
                CreateSelect2({
                    element: '#configuration_jobs_template_AD_HOC_COMMANDS',
                    multiple: true,
                    placeholder: 'Select commands',
                    opts: opts
                });
            }

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
