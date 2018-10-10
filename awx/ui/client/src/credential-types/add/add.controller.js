/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['Rest', 'Wait',
    'CredentialTypesForm', 'ProcessErrors', 'GetBasePath',
    'GenerateForm',  '$scope', '$state', 'Alert', 'GetChoices', 'ParseTypeChange', 'ToJSON', 'CreateSelect2', 'i18n',
    function(Rest, Wait,
        CredentialTypesForm, ProcessErrors, GetBasePath,
        GenerateForm, $scope, $state, Alert, GetChoices, ParseTypeChange, ToJSON, CreateSelect2, i18n
    ) {
        var form = CredentialTypesForm,
            url = GetBasePath('credential_types');

        init();

        function init() {

            // for add, don't show ssh
            $scope.$on('loadCredentialKindOptions', function() {
                $scope.credential_kind_options = $scope.credential_kind_options
                        .filter(val => val.value === 'net' ||
                            val.value === 'cloud');
            });

            // Load the list of options for Kind
            $scope.$parent.optionsDefer.promise
                .then(function(options) {
                    GetChoices({
                        scope: $scope,
                        url: url,
                        field: 'kind',
                        variable: 'credential_kind_options',
                        options: options,
                        callback: 'loadCredentialKindOptions'
                    });

                    const docs_url = 'https://docs.ansible.com/ansible-tower/latest/html/userguide/credential_types.html#getting-started-with-credential-types';
                    const docs_help_text = `<br><br><a href=${docs_url}>${i18n._('Getting Started with Credential Types')}</a>`;

                    const api_inputs_help_text = _.get(options, 'actions.POST.inputs.help_text', "Specification for credential type inputs.");
                    const api_injectors_help_text = _.get(options, 'actions.POST.injectors.help_text', "Specification for credential type injector.");

                    $scope.inputs_help_text = api_inputs_help_text + docs_help_text;
                    $scope.injectors_help_text = api_injectors_help_text + docs_help_text;

                    if (!options.actions.POST) {
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
                    kind: "cloud",
                    inputs: inputs,
                    injectors: injectors
                })
                .then(({data}) => {
                    $state.go('credentialTypes.edit', { credential_type_id: data.id }, { reload: true });
                    Wait('stop');
                })
                .catch(({data, status}) => {
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
