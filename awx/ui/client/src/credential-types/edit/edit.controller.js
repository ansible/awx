/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['Rest', 'Wait',
    'CredentialTypesForm', 'ProcessErrors', 'GetBasePath',
    'GenerateForm', 'resourceData',
    '$scope', '$state', 'GetChoices', 'ParseTypeChange', 'ToJSON', 'ParseVariableString', 'CreateSelect2',
    function(
        Rest, Wait, CredentialTypesForm, ProcessErrors, GetBasePath,
        GenerateForm, resourceData,
        $scope, $state, GetChoices, ParseTypeChange, ToJSON, ParseVariableString, CreateSelect2
    ) {
        var credential_typeData = resourceData.data,
            generator = GenerateForm,
            data = credential_typeData,
            id = credential_typeData.id,
            form = CredentialTypesForm,
            main = {},
            url = GetBasePath('credential_types');

        init();

        function init() {
            // Load the list of options for Kind
            $scope.$parent.optionsDefer.promise
                .then(function(options) {
                    GetChoices({
                        scope: $scope,
                        url: url,
                        field: 'kind',
                        variable: 'credential_kind_options',
                        options: options,
                        callback: 'choicesReadyCredentialTypes'
                    });

                    const docs_url = 'https://docs.ansible.com/ansible-tower/latest/html/userguide/credential_types.html#getting-started-with-credential-types';
                    const docs_help_text = `<br><br><a href=${docs_url}>Getting Started with Credential Types</a>`;

                    const api_inputs_help_text = _.get(options, 'actions.POST.inputs.help_text', "Specification for credential type inputs.");
                    const api_injectors_help_text = _.get(options, 'actions.POST.injectors.help_text', "Specification for credential type injector.");

                    $scope.inputs_help_text = api_inputs_help_text + docs_help_text;
                    $scope.injectors_help_text = api_injectors_help_text + docs_help_text;
                });
        }

        if ($scope.removeChoicesReady) {
            $scope.removeChoicesReady();
        }
        $scope.removeChoicesReady = $scope.$on('choicesReadyCredentialTypes',
            function() {

                if (!resourceData.data.managed_by_tower) {
                    $scope.credential_kind_options = $scope.credential_kind_options
                            .filter(val => val.value === 'net' ||
                                val.value === 'cloud');
                }

                $scope.credential_type = credential_typeData;

                $scope.parseTypeInputs = 'yaml';
                $scope.parseTypeInjectors = 'yaml';

                var callback = function() {
                    // Make sure the form controller knows there was a change
                    $scope[form.name + '_form'].$setDirty();
                };

                $scope.$watch('credential_type.summary_fields.user_capabilities.edit', function(val) {
                    if (val === false) {
                        $scope.canAdd = false;
                    }

                    let readOnly = !($scope.credential_type.summary_fields.user_capabilities.edit || $scope.canAdd);

                    ParseTypeChange({
                        scope: $scope,
                        field_id: 'credential_type_inputs',
                        variable: 'inputs',
                        onChange: callback,
                        parse_variable: 'parseTypeInputs',
                        readOnly: readOnly
                    });
                    ParseTypeChange({
                        scope: $scope,
                        field_id: 'credential_type_injectors',
                        variable: 'injectors',
                        onChange: callback,
                        parse_variable: 'parseTypeInjectors',
                        readOnly: readOnly
                    });
                });

                function getVars(str){

                    // Quick function to test if the host vars are a json-object-string,
                    // by testing if they can be converted to a JSON object w/o error.
                    function IsJsonString(str) {
                        try {
                            JSON.parse(str);
                        } catch (e) {
                            return false;
                        }
                        return true;
                    }

                    if(str === ''){
                        return '---';
                    }
                    else if(IsJsonString(str)){
                        str = JSON.parse(str);
                        return jsyaml.safeDump(str);
                    }
                    else if(!IsJsonString(str)){
                        return str;
                    }
                }

                var fld, i;
                for (fld in form.fields) {
                    if (data[fld]  && fld !== 'inputs' || fld !== 'injectors') {
                        $scope[fld] = data[fld];
                        main[fld] = data[fld];
                    }

                    if (fld === "kind") {
                        // Set kind field to the correct option
                        for (i = 0; i < $scope.credential_kind_options.length; i++) {
                            if ($scope.kind === $scope.credential_kind_options[i].value) {
                                $scope.kind = $scope.credential_kind_options[i];
                                main[fld] = $scope.credential_kind_options[i];
                                break;
                            }
                        }
                    }
                }

                $scope.inputs = ParseVariableString(getVars(data.inputs));
                $scope.injectors = ParseVariableString(getVars(data.injectors));

                CreateSelect2({
                    element: '#credential_type_kind',
                    multiple: false,
                });

                // if ($scope.inputs === "{}") {
                //     $scope.inputs = "---";
                // }
                //
                // if ($scope.injectors === "{}") {
                //     $scope.injectors = "---";
                // }

                // $scope.inputs = JSON.parse($scope.inputs);
                // $scope.injectors = JSON.parse($scope.injectors);

            }
        );

        $scope.formSave = function() {
            generator.clearApiErrors($scope);
            Wait('start');
            Rest.setUrl(url + id + '/');
            var inputs = ToJSON($scope.parseTypeInputs, $scope.inputs);
            var injectors = ToJSON($scope.parseTypeInjectors, $scope.injectors);
            if (inputs === null) {
              inputs = {};
            }
            if (injectors === null) {
              injectors = {};
            }
            Rest.put({
                    name: $scope.name,
                    description: $scope.description,
                    kind: "cloud",
                    inputs: inputs,
                    injectors: injectors
                })
                .then(() => {
                    $state.go($state.current, null, { reload: true });
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
            $state.go('credentialTypes');
        };

    }
];
