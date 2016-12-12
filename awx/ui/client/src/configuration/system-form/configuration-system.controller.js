/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$rootScope', '$scope', '$state', 'AngularCodeMirror', 'Authorization', 'ConfigurationSystemForm', 'ConfigurationService',
    'ConfigurationUtils', 'GenerateForm',
    function(
        $rootScope, $scope, $state, AngularCodeMirror, Authorization, ConfigurationSystemForm, ConfigurationService, ConfigurationUtils, GenerateForm
    ) {
        var systemVm = this;
        var generator = GenerateForm;
        var form = ConfigurationSystemForm;
        var keys = _.keys(form.fields);

        _.each(keys, function(key) {
            addFieldInfo(form, key);
        });

        // Disable the save button for system auditors
        form.buttons.save.disabled = $rootScope.user_is_system_auditor;

        function addFieldInfo(form, key) {
            _.extend(form.fields[key], {
                awPopOver: $scope.$parent.configDataResolve[key].help_text,
                label: $scope.$parent.configDataResolve[key].label,
                name: key,
                toggleSource: key,
                dataPlacement: 'top',
                dataTitle: $scope.$parent.configDataResolve[key].label,
                required: $scope.$parent.configDataResolve[key].required,
                ngDisabled: $rootScope.user_is_system_auditor
            });
        }

        generator.inject(form, {
            id: 'configure-system-form',
            mode: 'edit',
            scope: $scope.$parent,
            related: true
        });

        angular.extend(systemVm, {

        });
    }
];
