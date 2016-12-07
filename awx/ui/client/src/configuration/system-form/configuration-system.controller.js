/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$scope', '$state', 'AngularCodeMirror', 'ConfigurationSystemForm', 'ConfigurationService', 'ConfigurationUtils', 'GenerateForm', 'ParseTypeChange',
    function(
        $scope, $state, AngularCodeMirror, ConfigurationSystemForm, ConfigurationService, ConfigurationUtils, GenerateForm, ParseTypeChange
    ) {
        var systemVm = this;
        var generator = GenerateForm;
        var form = ConfigurationSystemForm;
        var keys = _.keys(form.fields);

        _.each(keys, function(key) {
            addFieldInfo(form, key);
        });

        // Disable the save button for non-superusers
        form.buttons.save.disabled = 'vm.updateProhibited';

        function addFieldInfo(form, key) {
            _.extend(form.fields[key], {
                awPopOver: $scope.$parent.configDataResolve[key].help_text,
                label: $scope.$parent.configDataResolve[key].label,
                name: key,
                toggleSource: key,
                dataPlacement: 'top',
                dataTitle: $scope.$parent.configDataResolve[key].label,
                required: $scope.$parent.configDataResolve[key].required
            });
        }

        generator.inject(form, {
            id: 'configure-system-form',
            mode: 'edit',
            scope: $scope.$parent,
            related: true
        });


        $scope.$on('populated', function() {
            // $scope.$parent.parseType = 'json';
            // ParseTypeChange({
            //     scope: $scope.$parent,
            //     variable: 'LICENSE',
            //     parse_variable: 'parseType',
            //     field_id: 'configuration_system_template_LICENSE',
            //     readOnly: true
            // });
        });

        angular.extend(systemVm, {

        });
    }
];
