/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$state', '$stateParams', '$scope', 'GroupForm', 'CredentialList', 'inventoryScriptsListObject', 'ParseTypeChange', 'GenerateForm', 'inventoryData', 'LookUpInit',
    'GroupManageService', 'GetChoices', 'GetBasePath', 'CreateSelect2', 'GetSourceTypeOptions',
    function($state, $stateParams, $scope, GroupForm, CredentialList, InventoryScriptsList, ParseTypeChange, GenerateForm, inventoryData, LookUpInit,
        GroupManageService, GetChoices, GetBasePath, CreateSelect2, GetSourceTypeOptions){
        var generator = GenerateForm,
            form = GroupForm();

        $scope.formCancel = function(){
            $state.go('^');
        };
        $scope.formSave = function(){
            var params, source;
            // group fields
            var group = {
                variables: $scope.variables === ('---' || '{}') ? null : $scope.variables,
                name: $scope.name,
                description: $scope.description,
                inventory: inventoryData.id
            };
            if ($scope.source){
                // inventory_source fields
                params = {
                    instance_filters: $scope.instance_filters,
                    source_vars: $scope[$scope.source.value + '_variables'] === ('---' || '{}') ? null : $scope[$scope.source.value + '_variables'],
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
            }
            else{
                source = null;
            }
            switch(source){
                // no inventory source set, just create a new group
                // '' is the value supplied for Manual source type
                case null || '':
                    GroupManageService.post(group).then(res => {
                        // associate
                        if ($stateParams.group){
                            return GroupManageService.associateGroup(res.data, _.last($stateParams.group))
                            .then(() => $state.go('^', null, {reload: true}));
                        }
                        else{
                            $state.go('^', null, {reload: true});
                        }
                    });
                    break;
                // create a new group and create/associate an inventory source
                // equal to case 'rax' || 'ec2' || 'azure' || 'azure_rm' || 'vmware' || 'foreman' || 'cloudforms' || 'openstack' || 'custom'
                default:
                    GroupManageService.post(group)
                        // associate to group
                        .then(res => {
                            if ($stateParams.group){
                                GroupManageService.associateGroup(res.data, _.last($stateParams.group));
                                return res;
                            }
                            else {return res;}
                            // pass the original POST response and not the association response
                        })
                        .then(res => GroupManageService.putInventorySource(
                            // put the received group ID into inventory source payload
                            // and pass the related endpoint
                            _.assign(params, {group: res.data.id}), res.data.related.inventory_source))
                        .then(res => $state.go('inventoryManage.editGroup', {group_id: res.data.group}, {reload: true}));
                    break;
            }
        };
        $scope.sourceChange = function(source){
            source = source.value === 'azure_rm' ? 'azure' : source.value;
            if (source === 'custom'){
                LookUpInit({
                    scope: $scope,
                    url: GetBasePath('inventory_script'),
                    form: form,
                    list: InventoryScriptsList,
                    field: 'inventory_script',
                    input_type: "radio"
                });
            }
            else if (source === 'ec2'){
                LookUpInit({
                    scope: $scope,
                    url: GetBasePath('credentials') + '?kind=aws',
                    form: form,
                    list: CredentialList,
                    field: 'credential',
                    input_type: "radio"
                });
            }
            // equal to case 'rax' || 'azure' || 'azure_rm' || 'vmware' || 'foreman' || 'cloudforms' || 'openstack' || 'custom'
            else{
                LookUpInit({
                    scope: $scope,
                    url: GetBasePath('credentials') + (source === '' ? '' : '?kind=' + source),
                    form: form,
                    list: CredentialList,
                    field: 'credential',
                    input_type: "radio"
                });
            }
            // reset fields
            $scope.group_by_choices = source === 'ec2' ? $scope.ec2_group_by : null;
            $scope.source_region_choices = $scope[source + '_regions'];
            $scope.cloudCredentialRequired = source !== 'manual' && source !== 'custom' ? true : false;
            $scope.group_by = null;
            $scope.source_regions = null;
            $scope.credential = null;
            $scope.credential_name = null;
            initRegionSelect();
        };
        var initRegionSelect = function(){
            CreateSelect2({
                element: '#group_source_regions',
                multiple: true
            });
            CreateSelect2({
                element: '#group_group_by',
                multiple: true
            });
        };
        var initSourceSelect = function(){
            CreateSelect2({
                element: '#group_source',
                multiple: false
            });
        };
        var initSources = function(){
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
        };
        // region / source options callback
        $scope.$on('choicesReadyGroup', function(){
            initRegionSelect();
        });

        $scope.$on('sourceTypeOptionsReady', function(){
            initSourceSelect();
        });
        var init = function(){
            $scope.parseType = 'yaml';
            $scope.variables = '---';
            generator.inject(form, {mode: 'add', related: false, id: 'Inventory-groupManage--panel', scope: $scope});
            ParseTypeChange({
                scope: $scope,
                field_id: 'group_variables',
                variable: 'variables',
            });
            initSources();
        };
        init();
    }];
