/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state', '$scope', 'ParseVariableString', 'ParseTypeChange',
    'GetChoices', 'GetBasePath', 'CreateSelect2', 'GetSourceTypeOptions',
    'SourcesService', 'inventoryData', 'inventorySourcesOptions', 'Empty',
    'Wait', 'Rest', 'Alert', '$rootScope', 'i18n', 'InventoryHostsStrings',
    'ProcessErrors', 'inventorySource', 'isNotificationAdmin', 'ConfigData',
    function($state, $scope, ParseVariableString, ParseTypeChange,
        GetChoices, GetBasePath, CreateSelect2, GetSourceTypeOptions,
        SourcesService, inventoryData, inventorySourcesOptions, Empty,
        Wait, Rest, Alert, $rootScope, i18n, InventoryHostsStrings,
        ProcessErrors, inventorySource, isNotificationAdmin, ConfigData) {

        const inventorySourceData = inventorySource.get();

        // To toggle notifications a user needs to have a read role on the inventory
        // _and_ have at least a notification template admin role on an org.
        // If the user has gotten this far it's safe to say they have
        // at least read access to the inventory
        $scope.sufficientRoleForNotifToggle = isNotificationAdmin;
        $scope.sufficientRoleForNotif =  isNotificationAdmin || $scope.user_is_system_auditor;
        $scope.projectBasePath = GetBasePath('projects') + '?not__status=never updated';
        $scope.canAdd = inventorySourcesOptions.actions.POST;
        const virtualEnvs = ConfigData.custom_virtualenvs || [];
        $scope.custom_virtualenvs_options = virtualEnvs;
        // instantiate expected $scope values from inventorySourceData
        _.assign($scope,
            {credential: inventorySourceData.credential},
            {overwrite: inventorySourceData.overwrite},
            {overwrite_vars: inventorySourceData.overwrite_vars},
            {update_on_launch: inventorySourceData.update_on_launch},
            {update_cache_timeout: inventorySourceData.update_cache_timeout},
            {inventory_script: inventorySourceData.source_script},
            {verbosity: inventorySourceData.verbosity});

        $scope.inventory_source_obj = inventorySourceData;
        $scope.breadcrumb.inventory_source_name = inventorySourceData.name;
        if (inventorySourceData.credential) {
            $scope.credential_name = inventorySourceData.summary_fields.credential.name;
        }

        if(inventorySourceData.source === 'scm') {
            $scope.project = inventorySourceData.source_project;
            $scope.project_name = inventorySourceData.summary_fields.source_project.name;
            updateSCMProject();
        }

        // display custom inventory_script name
        if (inventorySourceData.source === 'custom' && inventorySourceData.summary_fields.source_script) {
            $scope.inventory_script_name = inventorySourceData.summary_fields.source_script.name;
        }
        $scope = angular.extend($scope, inventorySourceData);

        $scope.$watch('summary_fields.user_capabilities.edit', function(val) {
            $scope.canAdd = val;
        });

        $scope.$on('sourceTypeOptionsReady', function() {
            $scope.source = _.find($scope.source_type_options, { value: inventorySourceData.source });
            var source = $scope.source && $scope.source.value ? $scope.source.value : null;
            $scope.cloudCredentialRequired = source !== '' && source !== 'scm' && source !== 'custom' && source !== 'ec2' ? true : false;
            CreateSelect2({
                element: '#inventory_source_source',
                multiple: false
            });

            if (true) {
                var varName;
                if (source === 'scm') {
                    varName = 'custom_variables';
                } else {
                    varName = source + '_variables';
                }

                $scope[varName] = ParseVariableString(inventorySourceData
                    .source_vars);

                ParseTypeChange({
                    scope: $scope,
                    field_id: varName,
                    variable: varName,
                    parse_variable: 'envParseType',
                    readOnly: !$scope.summary_fields.user_capabilities.edit
                });
            }
        });

        $scope.envParseType = 'yaml';

        GetSourceTypeOptions({
            scope: $scope,
            variable: 'source_type_options'
        });

        GetChoices({
            scope: $scope,
            field: 'verbosity',
            variable: 'verbosity_options',
            options: inventorySourcesOptions
        });

        var i;
        for (i = 0; i < $scope.verbosity_options.length; i++) {
            if ($scope.verbosity_options[i].value === $scope.verbosity) {
                $scope.verbosity = $scope.verbosity_options[i];
            }
        }

        CreateSelect2({
            element: '#inventory_source_custom_virtualenv',
            multiple: false,
            opts: $scope.custom_virtualenvs_options
        });

        initVerbositySelect();

        $scope.$watch('verbosity', initVerbositySelect);

        // Register a watcher on project_name
        if ($scope.getInventoryFilesUnregister) {
            $scope.getInventoryFilesUnregister();
        }
        $scope.getInventoryFilesUnregister = $scope.$watch('project', function (newValue, oldValue) {
            if (newValue !== oldValue) {
                updateSCMProject();
            }
        });

        function initVerbositySelect(){
            CreateSelect2({
                element: '#inventory_source_verbosity',
                multiple: false
            });
        }

        function sync_inventory_file_select2() {
            CreateSelect2({
                element:'#inventory-file-select',
                addNew: true,
                multiple: false,
                scope: $scope,
                options: 'inventory_files',
                model: 'inventory_file'
            });

            // TODO: figure out why the inventory file model is being set to
            // dirty
        }

        function updateSCMProject() {
            var url;

            if (!Empty($scope.project)) {
                url = GetBasePath('projects') + $scope.project + '/inventories/';
                Wait('start');
                Rest.setUrl(url);
                Rest.get()
                    .then(({data}) => {
                        $scope.inventory_files = data;
                        $scope.inventory_files.push("/ (project root)");

                        if (inventorySourceData.source_path !== "") {
                            $scope.inventory_file = inventorySourceData.source_path;
                            if ($scope.inventory_files.indexOf($scope.inventory_file) < 0) {
                                $scope.inventory_files.push($scope.inventory_file);
                            }
                        } else {
                            $scope.inventory_file = "/ (project root)";
                        }
                        sync_inventory_file_select2();
                        Wait('stop');
                    })
                    .catch(() => {
                        Alert('Cannot get inventory files', 'Unable to retrieve the list of inventory files for this project.', 'alert-info');
                        Wait('stop');
                    });
            }
        }

        $scope.lookupProject = function(){
            $state.go('.project', {
                project_search: {
                    page_size: '5',
                    page: '1'
                }
            });
        };

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

        $scope.formCancel = function() {
            $state.go('^');
        };
        $scope.formSave = function() {
            var params;

            console.log($scope);

            params = {
                id: inventorySourceData.id,
                name: $scope.name,
                description: $scope.description,
                inventory: inventoryData.id,
                source_script: $scope.inventory_script,
                credential: $scope.credential,
                overwrite: $scope.overwrite,
                overwrite_vars: $scope.overwrite_vars,
                update_on_launch: $scope.update_on_launch,
                update_cache_timeout: $scope.update_cache_timeout || 0,
                verbosity: $scope.verbosity.value,
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

            inventorySource.request('put', {
                data: params
            }).then(() => {
                $state.go('.', null, { reload: true });
            }).catch(({ data, status, config }) => {
                ProcessErrors($scope, data, status, null, {
                    hdr: 'Error!',
                    msg: InventoryHostsStrings.get('error.CALL', { path: `${config.url}`, status })
                });
            });
        };

        $scope.sourceChange = function(source) {
            source = (source && source.value) ? source.value : '';
            if ($scope.source.value === "scm" && $scope.source.value === "custom") {
                $scope.credentialBasePath = GetBasePath('credentials') + '?credential_type__kind__in=cloud,network';
            }
            else{
                $scope.credentialBasePath = (source === 'ec2') ? GetBasePath('credentials') + '?credential_type__namespace=aws' : GetBasePath('credentials') + (source === '' ? '' : 'credential_type__namespace=' + (source));
            }
            if (source === 'ec2' || source === 'custom' || source === 'vmware' || source === 'openstack' || source === 'scm' || source === 'cloudforms' || source === "satellite6") {
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

            $scope.cloudCredentialRequired = source !== '' && source !== 'scm' && source !== 'custom' && source !== 'ec2' ? true : false;
            $scope.credential = null;
            $scope.credential_name = null;
            $scope.overwrite_vars = false;
        };
    }
];
