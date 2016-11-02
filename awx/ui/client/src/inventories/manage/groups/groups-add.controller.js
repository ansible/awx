/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state', '$stateParams', '$scope', 'GroupForm', 'CredentialList', 'ParseTypeChange', 'GenerateForm', 'inventoryData',
                'GroupManageService', 'GetChoices', 'GetBasePath', 'CreateSelect2', 'GetSourceTypeOptions', 'rbacUiControlService', 'ToJSON',
                function($state, $stateParams, $scope, GroupForm, CredentialList,  ParseTypeChange, GenerateForm, inventoryData,
                         GroupManageService, GetChoices, GetBasePath, CreateSelect2, GetSourceTypeOptions, rbacUiControlService, ToJSON) {
                    var generator = GenerateForm,
                        form = GroupForm();
        init();

        function init() {
            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);

        rbacUiControlService.canAdd(GetBasePath('inventory') + $stateParams.inventory_id + "/groups")
            .then(function(canAdd) {
                $scope.canAdd = canAdd;
            });
            $scope.parseType = 'yaml';
            $scope.envParseType = 'yaml';
            ParseTypeChange({
                scope: $scope,
                field_id: 'group_variables',
                variable: 'variables',
            });
            initSources();
        }

        $scope.lookupCredential = function(){
            $state.go('.lookup.credential', {
                credential_search: {
                    kind: $scope.source.value,
                    page_size: '5',
                    page: '1'
                }
            });
        };

        $scope.formCancel = function() {
            $state.go('^');
        };

        $scope.formSave = function() {
            var params, source, json_data;
            json_data = ToJSON($scope.parseType, $scope.variables, true);
            // group fields
            var group = {
                variables: json_data,
                name: $scope.name,
                description: $scope.description,
                inventory: inventoryData.id
            };
            if ($scope.source) {
                // inventory_source fields
                params = {
                    instance_filters: $scope.instance_filters,
                    source_vars: $scope[$scope.source.value + '_variables'] === '---' || $scope[$scope.source.value + '_variables'] === '{}' ? null : $scope[$scope.source.value + '_variables'],
                    source_script: $scope.inventory_script,
                    source: $scope.source.value,
                    credential: $scope.credential,
                    overwrite: $scope.overwrite,
                    overwrite_vars: $scope.overwrite_vars,
                    update_on_launch: $scope.update_on_launch,
                    update_cache_timeout: $scope.update_cache_timeout || 0,
                    // comma-delimited strings
                    group_by: _.map($scope.group_by, 'value').join(','),
                    source_regions: _.map($scope.source_regions, 'value').join(',')
                };
                source = $scope.source.value;
            } else {
                source = null;
            }
            switch (source) {
                // no inventory source set, just create a new group
                // '' is the value supplied for Manual source type
                case null || '':
                    GroupManageService.post(group).then(res => {
                        // associate
                        if ($stateParams.group) {
                            return GroupManageService.associateGroup(res.data, _.last($stateParams.group))
                                .then(() => $state.go('^', null, { reload: true }));
                        } else {
                            $state.go('^', null, { reload: true });
                        }
                    });
                    break;
                    // create a new group and create/associate an inventory source
                    // equal to case 'rax' || 'ec2' || 'azure' || 'azure_rm' || 'vmware' || 'satellite6' || 'cloudforms' || 'openstack' || 'custom'
                default:
                    GroupManageService.post(group)
                        // associate to group
                        .then(res => {
                            if ($stateParams.group) {
                                GroupManageService.associateGroup(res.data, _.last($stateParams.group));
                                return res;
                            } else {
                                return res; }
                            // pass the original POST response and not the association response
                        })
                        .then(res => GroupManageService.putInventorySource(
                            // put the received group ID into inventory source payload
                            // and pass the related endpoint
                            _.assign(params, { group: res.data.id }), res.data.related.inventory_source))
                        .then(res => $state.go('inventoryManage.editGroup', { group_id: res.data.group }, { reload: true }));
                    break;
            }
        };
        $scope.sourceChange = function(source) {
            source = source.value;
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
                element: '#group_source_regions',
                multiple: true
            });
            CreateSelect2({
                element: '#group_group_by',
                multiple: true
            });
        }
        function initSourceSelect(){
            CreateSelect2({
                element: '#group_source',
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
