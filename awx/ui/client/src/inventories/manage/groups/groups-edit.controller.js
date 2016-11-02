/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state', '$stateParams', '$scope', 'ToggleNotification', 'ParseVariableString',
                'ParseTypeChange', 'GroupManageService', 'GetChoices', 'GetBasePath', 'CreateSelect2', 'GetSourceTypeOptions', 'groupData', 'inventorySourceData', 'ToJSON',
                function($state, $stateParams, $scope, ToggleNotification, ParseVariableString,
                         ParseTypeChange, GroupManageService, GetChoices, GetBasePath, CreateSelect2, GetSourceTypeOptions, groupData, inventorySourceData, ToJSON) {

        init();

        function init() {
            // instantiate expected $scope values from inventorySourceData & groupData
            _.assign($scope, { credential: inventorySourceData.credential }, { overwrite: inventorySourceData.overwrite }, { overwrite_vars: inventorySourceData.overwrite_vars }, { update_on_launch: inventorySourceData.update_on_launch }, { update_cache_timeout: inventorySourceData.update_cache_timeout }, { instance_filters: inventorySourceData.instance_filters }, { inventory_script: inventorySourceData.source_script });
            if (inventorySourceData.credential) {
                $scope.credential_name = inventorySourceData.summary_fields.credential.name;
            }
            $scope = angular.extend($scope, groupData);

            // display custom inventory_script name
            if (inventorySourceData.source === 'custom') {
                $scope.inventory_script_name = inventorySourceData.summary_fields.source_script.name;
            }

            $scope.$watch('summary_fields.user_capabilities.edit', function(val) {
                $scope.canAdd = val;
            });

            // init codemirror(s)
            $scope.variables = $scope.variables === null || $scope.variables === '' ? '---' : ParseVariableString($scope.variables);
            $scope.parseType = 'yaml';
            $scope.envParseType = 'yaml';

            ParseTypeChange({
                scope: $scope,
                field_id: 'group_variables',
                variable: 'variables',
            });

            initSources();
        }

        var initRegionSelect = function() {
            CreateSelect2({
                element: '#group_source_regions',
                multiple: true
            });
            CreateSelect2({
                element: '#group_group_by',
                multiple: true
            });
        };

        $scope.formCancel = function() {
            $state.go('^');
        };
        $scope.formSave = function() {
            var params, source;
            json_data = ToJSON($scope.parseType, $scope.variables, true);
            // group fields
            var group = {
                variables: json_data,
                name: $scope.name,
                description: $scope.description,
                inventory: $scope.inventory,
                id: groupData.id
            };
            if ($scope.source) {
                // inventory_source fields
                params = {
                    group: groupData.id,
                    source: $scope.source.value,
                    credential: $scope.credential,
                    overwrite: $scope.overwrite,
                    overwrite_vars: $scope.overwrite_vars,
                    source_script: $scope.inventory_script,
                    update_on_launch: $scope.update_on_launch,
                    update_cache_timeout: $scope.update_cache_timeout || 0,
                    // comma-delimited strings
                    group_by: _.map($scope.group_by, 'value').join(','),
                    source_regions: _.map($scope.source_regions, 'value').join(','),
                    instance_filters: $scope.instance_filters,
                    source_vars: $scope[$scope.source.value + '_variables'] === '---' || $scope[$scope.source.value + '_variables'] === '{}' ? null : $scope[$scope.source.value + '_variables']
                };
                source = $scope.source.value;
            } else {
                source = null;
            }
            switch (source) {
                // no inventory source set, just create a new group
                // '' is the value supplied for Manual source type
                case null || '':
                    GroupManageService.put(group).then(() => $state.go($state.current, null, { reload: true }));
                    break;
                    // create a new group and create/associate an inventory source
                    // equal to case 'rax' || 'ec2' || 'azure' || 'azure_rm' || 'vmware' || 'satellite6' || 'cloudforms' || 'openstack' || 'custom'
                default:
                    GroupManageService.put(group)
                        .then(() => GroupManageService.putInventorySource(params, groupData.related.inventory_source))
                        .then(() => $state.go($state.current, null, { reload: true }));
                    break;
            }
        };

        $scope.sourceChange = function(source) {
            $scope.source = source;
            if (source.value === 'ec2' || source.value === 'custom' ||
                source.value === 'vmware' || source.value === 'openstack') {
                $scope[source.value + '_variables'] = $scope[source.value + '_variables'] === null ? '---' : $scope[source.value + '_variables'];
                ParseTypeChange({
                    scope: $scope,
                    field_id: source.value + '_variables',
                    variable: source.value + '_variables',
                    parse_variable: 'envParseType',
                });
            }
            // reset fields
            // azure_rm regions choices are keyed as "azure" in an OPTIONS request to the inventory_sources endpoint
            $scope.source_region_choices = source.value === 'azure_rm' ? $scope.azure_regions : $scope[source.value + '_regions'];
            $scope.cloudCredentialRequired = source.value !== '' && source.value !== 'custom' && source.value !== 'ec2' ? true : false;
            $scope.group_by = null;
            $scope.source_regions = null;
            $scope.credential = null;
            $scope.credential_name = null;
            initRegionSelect();
        };

        function initSourceSelect() {
            $scope.source = _.find($scope.source_type_options, { value: inventorySourceData.source });
            CreateSelect2({
                element: '#group_source',
                multiple: false
            });
            // After the source is set, conditional fields will be visible
            // CodeMirror is buggy if you instantiate it in a not-visible element
            // So we initialize it here instead of the init() routine
            if (inventorySourceData.source === 'ec2' || inventorySourceData.source === 'openstack' ||
                inventorySourceData.source === 'custom' || inventorySourceData.source === 'vmware') {
                $scope[inventorySourceData.source + '_variables'] = inventorySourceData.source_vars === null || inventorySourceData.source_vars === '' ? '---' : ParseVariableString(inventorySourceData.source_vars);
                ParseTypeChange({
                    scope: $scope,
                    field_id: inventorySourceData.source + '_variables',
                    variable: inventorySourceData.source + '_variables',
                    parse_variable: 'envParseType',
                });
            }
        }

        function initRegionData() {
            var source = $scope.source.value === 'azure_rm' ? 'azure' : $scope.source.value;
            var regions = inventorySourceData.source_regions.split(',');
            // azure_rm regions choices are keyed as "azure" in an OPTIONS request to the inventory_sources endpoint
            $scope.source_region_choices = $scope[source + '_regions'];

            // the API stores azure regions as all-lowercase strings - but the azure regions received from OPTIONS are Snake_Cased
            if (source === 'azure') {
                $scope.source_regions = _.map(regions, (region) => _.find($scope[source + '_regions'], (o) => o.value.toLowerCase() === region));
            }
            // all other regions are 1-1
            else {
                $scope.source_regions = _.map(regions, (region) => _.find($scope[source + '_regions'], (o) => o.value === region));
            }
            $scope.group_by_choices = source === 'ec2' ? $scope.ec2_group_by : null;
            if (source === 'ec2') {
                var group_by = inventorySourceData.group_by.split(',');
                $scope.group_by = _.map(group_by, (item) => _.find($scope.ec2_group_by, { value: item }));
            }
            initRegionSelect();
        }

        function initSources() {
            GetSourceTypeOptions({
                scope: $scope,
                variable: 'source_type_options',
                //callback: 'sourceTypeOptionsReady' this callback is hard-coded into GetSourceTypeOptions(), included for ref
            });
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
            GetChoices({
                scope: $scope,
                url: GetBasePath('inventory_sources'),
                field: 'group_by',
                variable: 'ec2_group_by',
                choice_name: 'ec2_group_by_choices',
                callback: 'choicesReadyGroup'
            });
        }

        // region / source options callback
        $scope.$on('choicesReadyGroup', function() {
            if (angular.isObject($scope.source)) {
                initRegionData();
            }
        });

        $scope.$on('sourceTypeOptionsReady', function() {
            initSourceSelect();
        });
    }
];
