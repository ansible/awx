/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state', '$stateParams', '$scope', 'SourcesFormDefinition',
    'ParseTypeChange', 'GenerateForm', 'inventoryData', 'GroupManageService',
    'GetChoices', 'GetBasePath', 'CreateSelect2', 'GetSourceTypeOptions',
    'rbacUiControlService', 'ToJSON', 'SourcesService',
    function($state, $stateParams, $scope, SourcesFormDefinition,  ParseTypeChange,
        GenerateForm, inventoryData, GroupManageService, GetChoices,
        GetBasePath, CreateSelect2, GetSourceTypeOptions, rbacUiControlService,
        ToJSON, SourcesService) {

        let form = SourcesFormDefinition;
        init();

        function init() {
            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);

        rbacUiControlService.canAdd(GetBasePath('inventory') + $stateParams.inventory_id + "/inventory_sources")
            .then(function(canAdd) {
                $scope.canAdd = canAdd;
            });
            $scope.envParseType = 'yaml';
            initSources();
        }

        $scope.lookupCredential = function(){
            let kind = ($scope.source.value === "ec2") ? "aws" : $scope.source.value;
            $state.go('.credential', {
                credential_search: {
                    kind: kind,
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
                update_cache_timeout: $scope.update_cache_timeout || 0,
                // comma-delimited strings
                group_by: _.map($scope.group_by, 'value').join(','),
                source_regions: _.map($scope.source_regions, 'value').join(',')
            };

            if ($scope.source) {
                params.source_vars = $scope[$scope.source.value + '_variables'] === '---' || $scope[$scope.source.value + '_variables'] === '{}' ? null : $scope[$scope.source.value + '_variables'];
                params.source = $scope.source.value;
            } else {
                params.source = null;
            }
            SourcesService.post(params).then(function(res){
                let inventory_source_id = res.data.id;
                $state.go('^.edit', {inventory_source_id: inventory_source_id}, {reload: true});
            });
        };
        $scope.sourceChange = function(source) {
            source = source.value;
            if (source === 'custom'){
                $scope.credentialBasePath = GetBasePath('inventory_script');
            }
            // equal to case 'ec2' || 'rax' || 'azure' || 'azure_rm' || 'vmware' || 'satellite6' || 'cloudforms' || 'openstack'
            else{
                $scope.credentialBasePath = (source === 'ec2') ? GetBasePath('credentials') + '?kind=aws' : GetBasePath('credentials') + (source === '' ? '' : '?kind=' + (source));
            }
            if (source === 'ec2' || source === 'custom' || source === 'vmware' || source === 'openstack') {
                ParseTypeChange({
                    scope: $scope,
                    field_id: source + '_variables',
                    variable: source + '_variables',
                    parse_variable: 'envParseType'
                });
            }

            // reset fields
            $scope.group_by_choices = source === 'ec2' ? $scope.ec2_group_by : null;
            // azure_rm regions choices are keyed as "azure" in an OPTIONS request to the inventory_sources endpoint
            $scope.source_region_choices = source === 'azure_rm' ? $scope.azure_regions : $scope[source + '_regions'];
            $scope.cloudCredentialRequired = source !== '' && source !== 'custom' && source !== 'ec2' ? true : false;
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
            GetSourceTypeOptions({
                scope: $scope,
                variable: 'source_type_options',
                //callback: 'sourceTypeOptionsReady' this callback is hard-coded into GetSourceTypeOptions(), included for ref
            });
        }
    }
];
