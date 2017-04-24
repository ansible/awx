/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['Rest', 'Wait',
    'CredentialTypesForm', 'ProcessErrors', 'GetBasePath',
    'GenerateForm',  '$scope', '$state', 'Alert', 'GetChoices', 'ParseTypeChange', 'ToJSON', 'CreateSelect2',
    function(Rest, Wait,
        CredentialTypesForm, ProcessErrors, GetBasePath,
        GenerateForm, $scope, $state, Alert, GetChoices, ParseTypeChange, ToJSON, CreateSelect2
    ) {
        var form = CredentialTypesForm,
            url = GetBasePath('credential_types');

        init();

        function init() {
            // Load the list of options for Kind
            GetChoices({
                scope: $scope,
                url: url,
                field: 'kind',
                variable: 'credential_kind_options'
            });

            Rest.setUrl(url);
            Rest.options()
                .success(function(data) {
                    if (!data.actions.POST) {
                        $state.go("^");
                        Alert('Permission Error', 'You do not have permission to add a credential type.', 'alert-info');
                    }
                });

            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);

            // @issue @jmitchell - this setting probably collides with new RBAC can* implementation?
            $scope.canEdit = true;

            var callback = function() {
                // Make sure the form controller knows there was a change
                $scope[form.name + '_form'].$setDirty();
            };
            $scope.parseTypeInputs = 'yaml';
            $scope.parseTypeInjectors = 'yaml';
            ParseTypeChange({
                scope: $scope,
                field_id: 'credential_type_inputs',
                variable: 'inputs',
                onChange: callback,
                parse_variable: 'parseTypeInputs'
            });
            ParseTypeChange({
                scope: $scope,
                field_id: 'credential_type_injectors',
                variable: 'injectors',
                onChange: callback,
                parse_variable: 'parseTypeInjectors'
            });

            CreateSelect2({
                element: '#credential_type_kind',
                multiple: false,
            });
        }

        // Save
        $scope.formSave = function() {
            GenerateForm.clearApiErrors($scope);
            Wait('start');
            Rest.setUrl(url);
            var inputs = ToJSON($scope.parseTypeInputs, $scope.inputs);
            var injectors = ToJSON($scope.parseTypeInjectors, $scope.injectors);
            if (inputs === null) {
              inputs = {};
            }
            if (injectors === null) {
              injectors = {};
            }
            Rest.post({
                    name: $scope.name,
                    description: $scope.description,
                    kind: $scope.kind.value,
                    inputs: inputs,
                    injectors: injectors
                })
                .success(function(data) {
                    $state.go('credentialTypes.edit', { credential_type_id: data.id }, { reload: true });
                    Wait('stop');
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to add new credential type. PUT returned status: ' + status
                    });
                });
        };

        $scope.formCancel = function() {
            $state.go('^');
        };
    }
];
