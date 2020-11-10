/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state', 'ConfigData', '$scope', 'SourcesFormDefinition', 'ParseTypeChange', 
    'GenerateForm', 'inventoryData', 'GetChoices', 
    'GetBasePath', 'CreateSelect2', 'GetSourceTypeOptions',
    'SourcesService', 'Empty', 'Wait', 'Rest', 'Alert', 'ProcessErrors', 
    'inventorySourcesOptions', '$rootScope', 'i18n', 'InventorySourceModel', 'InventoryHostsStrings',
    function($state, ConfigData, $scope, SourcesFormDefinition,  ParseTypeChange,
        GenerateForm, inventoryData, GetChoices,
        GetBasePath, CreateSelect2, GetSourceTypeOptions,
        SourcesService, Empty, Wait, Rest, Alert, ProcessErrors,
        inventorySourcesOptions,$rootScope, i18n, InventorySource, InventoryHostsStrings) {

        let form = SourcesFormDefinition;
        $scope.mode = 'add';
        // apply form definition's default field values
        GenerateForm.applyDefaults(form, $scope, true);
        $scope.canAdd = inventorySourcesOptions.actions.POST;
        $scope.envParseType = 'yaml';
        const virtualEnvs = ConfigData.custom_virtualenvs || [];
        $scope.custom_virtualenvs_options = virtualEnvs;

        GetChoices({
            scope: $scope,
            field: 'verbosity',
            variable: 'verbosity_options',
            options: inventorySourcesOptions
        });

        CreateSelect2({
            element: '#inventory_source_verbosity',
            multiple: false
        });

        $scope.verbosity = $scope.verbosity_options[1];

        CreateSelect2({
            element: '#inventory_source_custom_virtualenv',
            multiple: false,
            opts: $scope.custom_virtualenvs_options
        });

        GetSourceTypeOptions({
            scope: $scope,
            variable: 'source_type_options'
        });

        const inventorySource = new InventorySource();

        var getInventoryFiles = function (project) {
            var url;

            if (!Empty(project)) {
                url = GetBasePath('projects') + project + '/inventories/';
                Wait('start');
                Rest.setUrl(url);
                Rest.get()
                    .then(({data}) => {
                        $scope.inventory_files = data;
                        $scope.inventory_files.push("/ (project root)");
                        CreateSelect2({
                            element:'#inventory-file-select',
                            addNew: true,
                            multiple: false,
                            scope: $scope,
                            options: 'inventory_files',
                            model: 'inventory_file'
                        });
                        Wait('stop');
                    })
                    .catch(() => {
                        Alert('Cannot get inventory files', 'Unable to retrieve the list of inventory files for this project.', 'alert-info');
                        Wait('stop');
                    });
            }
        };

        // Register a watcher on project_name
        if ($scope.getInventoryFilesUnregister) {
            $scope.getInventoryFilesUnregister();
        }
        $scope.getInventoryFilesUnregister = $scope.$watch('project', function (newValue, oldValue) {
            if (newValue !== oldValue) {
                getInventoryFiles(newValue);
            }
        });

        $scope.lookupCredential = function(){
            // For most source type selections, we filter for 1-1 matches to credential_type namespace.
            let searchKey = 'credential_type__namespace';
            let searchValue = $scope.source.value;

            // SCM and custom source types are more generic in terms of the credentials they
            // accept - any cloud or user-defined credential type can be used. We filter for
            // these using the credential_type kind field, which categorizes all cloud and
            // user-defined credentials as 'cloud'.
            if ($scope.source.value === 'scm') {
                searchKey = 'credential_type__kind';
                searchValue = 'cloud';
            }

            if ($scope.source.value === 'custom') {
                searchKey = 'credential_type__kind';
                searchValue = 'cloud';
            }

            // When the selection is 'ec2' we actually want to filter for the 'aws' namespace.
            if ($scope.source.value === 'ec2') {
                searchValue = 'aws';
            }

            $state.go('.credential', {
                credential_search: {
                    [searchKey]: searchValue,
                    page_size: '5',
                    page: '1'
                }
            });
        };

        $scope.lookupProject = function(){
            $state.go('.project', {
                project_search: {
                    page_size: '5',
                    page: '1'
                }
            });
        };

        $scope.sourceChange = function(source) {
            source = (source && source.value) ? source.value : '';
            if ($scope.source.value === "scm" && $scope.source.value === "custom") {
                $scope.credentialBasePath = GetBasePath('credentials') + '?credential_type__kind__in=cloud,network';
            }
            else{
                $scope.credentialBasePath = (source === 'ec2') ? GetBasePath('credentials') + '?credential_type__namespace=aws' : GetBasePath('credentials') + (source === '' ? '' : '?credential_type__namespace=' + (source));
            }
            if (true) {
                $scope.envParseType = 'yaml';

                var varName;
                if (source === 'scm') {
                    varName = 'custom_variables';
                } else {
                    varName = source + '_variables';
                }

                $scope[varName] = $scope[varName] === (null || undefined) ? '---' : $scope[varName];
                ParseTypeChange({
                    scope: $scope,
                    field_id: varName,
                    variable: varName,
                    parse_variable: 'envParseType'
                });
            }

            if (source === 'scm') {
                $scope.projectBasePath = GetBasePath('projects')  + '?not__status=never updated';
            }

            $scope.cloudCredentialRequired = source !== '' && source !== 'scm' && source !== 'custom' && source !== 'ec2' ? true : false;
            $scope.credential = null;
            $scope.credential_name = null;
            $scope.overwrite_vars = false;
        };

        $scope.$on('sourceTypeOptionsReady', function() {
            CreateSelect2({
                element: '#inventory_source_source',
                multiple: false
            });
        });

        $scope.formCancel = function() {
            $state.go('^');
        };

        $scope.formSave = function() {
            var params;

            params = {
                name: $scope.name,
                description: $scope.description,
                inventory: inventoryData.id,
                source_script: $scope.inventory_script,
                credential: $scope.credential,
                overwrite: $scope.overwrite,
                overwrite_vars: $scope.overwrite_vars,
                update_on_launch: $scope.update_on_launch,
                verbosity: $scope.verbosity.value,
                update_cache_timeout: $scope.update_cache_timeout || 0,
                custom_virtualenv: $scope.custom_virtualenv || null,
                enabled_var: $scope.enabled_var,
                enabled_value: $scope.enabled_value,
                host_filter: $scope.host_filter
            };

            if ($scope.source) {
                let source_vars = $scope.source.value === 'scm' ? $scope.custom_variables : $scope[$scope.source.value + '_variables'];
                params.source_vars = source_vars === '---' || source_vars === '{}' ? null : source_vars;
                params.source = $scope.source.value;
                if ($scope.source.value === 'scm') {
                  params.update_on_project_update = $scope.update_on_project_update;
                  params.source_project = $scope.project;

                  if ($scope.inventory_file === '/ (project root)') {
                      params.source_path = "";
                  } else {
                      params.source_path = $scope.inventory_file;
                  }
                }
            } else {
                params.source = null;
            }

            inventorySource.request('post', {
                data: params
            }).then((response) => {
                let inventory_source_id = response.data.id;
                $state.go('^.edit', {inventory_source_id: inventory_source_id}, {reload: true});
            }).catch(({ data, status, config }) => {
                ProcessErrors($scope, data, status, null, {
                    hdr: 'Error!',
                    msg: InventoryHostsStrings.get('error.CALL', { path: `${config.url}`, status })
                });
            });
        };
    }
];
