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
            id: 'configure-system-form',
            mode: 'edit',
            scope: $scope.$parent,
            related: true
        });


        $scope.$on('populated', function() {

            // var fld = 'LICENSE';
            // var readOnly = true;
            // $scope.$parent[fld + 'codeMirror'] = AngularCodeMirror(readOnly);
            // $scope.$parent[fld + 'codeMirror'].addModes($AnsibleConfig.variable_edit_modes);
            // $scope.$parent[fld + 'codeMirror'].showTextArea({
            //     scope: $scope.$parent,
            //     model: fld,
            //     element: "configuration_system_template_LICENSE",
            //     lineNumbers: true,
            //     mode: 'json',
            // });

            $scope.$parent.parseType = 'json';
            ParseTypeChange({
                scope: $scope.$parent,
                variable: 'LICENSE',
                parse_variable: 'parseType',
                field_id: 'configuration_system_template_LICENSE',
                readOnly: true
            });
        });

        angular.extend(systemVm, {

        });
    }
];
