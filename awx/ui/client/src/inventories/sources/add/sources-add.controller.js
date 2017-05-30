/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state', '$stateParams', '$scope', 'SourcesFormDefinition',
    'ParseTypeChange', 'GenerateForm', 'inventoryData', 'GroupManageService',
    'GetChoices', 'GetBasePath', 'CreateSelect2', 'GetSourceTypeOptions',
    'rbacUiControlService', 'ToJSON', 'SourcesService', 'canAdd', 'Empty',
    'Wait', 'Rest', 'Alert', 'ProcessErrors',
    function($state, $stateParams, $scope, SourcesFormDefinition,  ParseTypeChange,
        GenerateForm, inventoryData, GroupManageService, GetChoices,
        GetBasePath, CreateSelect2, GetSourceTypeOptions, rbacUiControlService,
        ToJSON, SourcesService, canAdd, Empty, Wait, Rest, Alert, ProcessErrors) {

        let form = SourcesFormDefinition;
        init();

        function init() {
            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);
            $scope.canAdd = canAdd;
            $scope.envParseType = 'yaml';
            initSources();
        }

        var getInventoryFiles = function (project) {
            var url;

            if (!Empty(project)) {
                url = GetBasePath('projects') + project + '/inventories/';
                Wait('start');
                Rest.setUrl(url);
                Rest.get()
                    .success(function (data) {
                        $scope.inventory_files = data;
                        $scope.inventory_files.push("/ (project root)");
                        sync_inventory_file_select2();
                        Wait('stop');
                    })
                    .error(function () {
                        Alert('Cannot get inventory files', 'Unable to retrieve the list of inventory files for this project.', 'alert-info');
                        Wait('stop');
                    });
            }
        };

        // Detect and alert user to potential SCM status issues
        var checkSCMStatus = function () {
            if (!Empty($scope.project)) {
                Rest.setUrl(GetBasePath('projects') + $scope.project + '/');
                Rest.get()
                    .success(function (data) {
                        var msg;
                        switch (data.status) {
                        case 'failed':
                            msg = "<div>The Project selected has a status of \"failed\". You must run a successful update before you can select an inventory file.";
                            break;
                        case 'never updated':
                            msg = "<div>The Project selected has a status of \"never updated\". You must run a successful update before you can select an inventory file.";
                            break;
                        case 'missing':
                            msg = '<div>The selected project has a status of \"missing\". Please check the server and make sure ' +
                                ' the directory exists and file permissions are set correctly.</div>';
                            break;
                        }
                        if (msg) {
                            Alert('Warning', msg, 'alert-info alert-info--noTextTransform', null, null, null, null, true);
                        }
                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                            msg: 'Failed to get project ' + $scope.project + '. GET returned status: ' + status });
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
                checkSCMStatus();
            }
        });

        function sync_inventory_file_select2() {
            CreateSelect2({
                element:'#inventory-file-select',
                addNew: true,
                multiple: false,
                scope: $scope,
                options: 'inventory_files',
                model: 'inventory_file'
            });
        }

        $scope.lookupCredential = function(){
            $state.go('.credential', {
                credential_search: {
                    // TODO: get kind sorting for credential properly implemented
                    // kind: kind,
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

        $scope.projectBasePath = GetBasePath('projects');
        $scope.credentialBasePath = GetBasePath('credentials') + '?credential_type__kind__in=cloud,network';

        $scope.sourceChange = function(source) {
            if (source) {
              source = source.value;
            } else {
              source = "";
            }

            $scope.credentialBasePath = GetBasePath('credentials') + '?credential_type__kind__in=cloud,network';

            if (source === 'custom'){
                $scope.credentialBasePath = GetBasePath('inventory_script');
            }

            if (source === 'ec2' || source === 'custom' || source === 'vmware' || source === 'openstack' || source === 'scm') {
                $scope.envParseType = 'yaml';

                var varName;
                if (source === 'scm') {
                    varName = 'custom_variables';
                } else {
                    varName = source + '_variables';
                }

                ParseTypeChange({
                    scope: $scope,
                    field_id: varName,
                    variable: varName,
                    parse_variable: 'envParseType'
                });
            }

            if (source === 'scm') {
              $scope.overwrite_vars = true;
              $scope.inventory_source_form.inventory_file.$setPristine();
            } else {
              $scope.overwrite_vars = false;
            }

            // reset fields
            $scope.group_by_choices = source === 'ec2' ? $scope.ec2_group_by : null;
            // azure_rm regions choices are keyed as "azure" in an OPTIONS request to the inventory_sources endpoint
            $scope.source_region_choices = source === 'azure_rm' ? $scope.azure_regions : $scope[source + '_regions'];
            $scope.cloudCredentialRequired = source !== '' && source !== 'scm' && source !== 'custom' && source !== 'ec2' ? true : false;
            $scope.group_by = null;
            $scope.source_regions = null;
            $scope.credential = null;
            $scope.credential_name = null;
            initRegionSelect();
        };
        // region / source options callback
        $scope.$on('choicesReadyGroup', function() {
            initRegionSelect();
        });

        $scope.$on('choicesReadyVerbosity', function() {
            initVerbositySelect();
        });

        $scope.$on('sourceTypeOptionsReady', function() {
            initSourceSelect();
        });

        function initRegionSelect(){
            CreateSelect2({
                element: '#inventory_source_source_regions',
                multiple: true
            });
            CreateSelect2({
                element: '#inventory_source_group_by',
                multiple: true
            });
        }

        function initSourceSelect(){
            CreateSelect2({
                element: '#inventory_source_source',
                multiple: false
            });
        }

        function initVerbositySelect(){
            CreateSelect2({
                element: '#inventory_source_verbosity',
                multiple: false
            });

            $scope.verbosity = $scope.verbosity_options[0];
        }

        function initSources(){
            GetChoices({
                scope: $scope,
                url: GetBasePath('inventory_sources'),
                field: 'source_regions',
                variable: 'rax_regions',
                choice_name: 'rax_region_choices',
                callback: 'choicesReadyGroup'
            });

            GetChoices({
                scope: $scope,
                url: GetBasePath('inventory_sources'),
                field: 'source_regions',
                variable: 'ec2_regions',
                choice_name: 'ec2_region_choices',
                callback: 'choicesReadyGroup'
            });

            GetChoices({
                scope: $scope,
                url: GetBasePath('inventory_sources'),
                field: 'source_regions',
                variable: 'gce_regions',
                choice_name: 'gce_region_choices',
                callback: 'choicesReadyGroup'
            });

            GetChoices({
                scope: $scope,
                url: GetBasePath('inventory_sources'),
                field: 'source_regions',
                variable: 'azure_regions',
                choice_name: 'azure_region_choices',
                callback: 'choicesReadyGroup'
            });

            // Load options for group_by
            GetChoices({
                scope: $scope,
                url: GetBasePath('inventory_sources'),
                field: 'group_by',
                variable: 'ec2_group_by',
                choice_name: 'ec2_group_by_choices',
                callback: 'choicesReadyGroup'
            });

            GetChoices({
                scope: $scope,
                url: GetBasePath('inventory_sources'),
                field: 'verbosity',
                variable: 'verbosity_options',
                callback: 'choicesReadyVerbosity'
            });

            GetSourceTypeOptions({
                scope: $scope,
                variable: 'source_type_options',
                //callback: 'sourceTypeOptionsReady' this callback is hard-coded into GetSourceTypeOptions(), included for ref
            });
        }

        $scope.formCancel = function() {
            $state.go('^');
        };

        $scope.formSave = function() {
            var params;

            params = {
                name: $scope.name,
                description: $scope.description,
                inventory: inventoryData.id,
                instance_filters: $scope.instance_filters,
                source_script: $scope.inventory_script,
                credential: $scope.credential,
                overwrite: $scope.overwrite,
                overwrite_vars: $scope.overwrite_vars,
                update_on_launch: $scope.update_on_launch,
                verbosity: $scope.verbosity.value,
                update_cache_timeout: $scope.update_cache_timeout || 0,
                // comma-delimited strings
                group_by: _.map($scope.group_by, 'value').join(','),
                source_regions: _.map($scope.source_regions, 'value').join(',')
            };

            if ($scope.source) {
                params.source_vars = $scope[$scope.source.value + '_variables'] === '---' || $scope[$scope.source.value + '_variables'] === '{}' ? null : $scope[$scope.source.value + '_variables'];
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
            SourcesService.post(params).then(function(res){
                let inventory_source_id = res.data.id;
                $state.go('^.edit', {inventory_source_id: inventory_source_id}, {reload: true});
            });
        };
    }
];
