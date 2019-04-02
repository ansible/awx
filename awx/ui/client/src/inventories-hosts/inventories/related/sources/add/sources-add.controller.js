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
            field: 'source_regions',
            variable: 'rax_regions',
            choice_name: 'rax_region_choices',
            options: inventorySourcesOptions
        });

        GetChoices({
            scope: $scope,
            field: 'source_regions',
            variable: 'ec2_regions',
            choice_name: 'ec2_region_choices',
            options: inventorySourcesOptions
        });

        GetChoices({
            scope: $scope,
            field: 'source_regions',
            variable: 'gce_regions',
            choice_name: 'gce_region_choices',
            options: inventorySourcesOptions
        });

        GetChoices({
            scope: $scope,
            field: 'source_regions',
            variable: 'azure_regions',
            choice_name: 'azure_rm_region_choices',
            options: inventorySourcesOptions
        });

        // Load options for group_by
        GetChoices({
            scope: $scope,
            field: 'group_by',
            variable: 'ec2_group_by',
            choice_name: 'ec2_group_by_choices',
            options: inventorySourcesOptions
        });

        initRegionSelect();

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
            if($scope.source.value !== "scm" && $scope.source.value !== "custom") {
                let kind = ($scope.source.value === "ec2") ? "aws" : $scope.source.value;
                $state.go('.credential', {
                    credential_search: {
                        kind: kind,
                        page_size: '5',
                        page: '1'
                    }
                });
            }
            else {
                $state.go('.credential', {
                    credential_search: {
                        credential_type__kind: "cloud",
                        page_size: '5',
                        page: '1'
                    }
                });
            }
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
                $scope.credentialBasePath = (source === 'ec2') ? GetBasePath('credentials') + '?kind=aws' : GetBasePath('credentials') + (source === '' ? '' : '?kind=' + (source));
            }
            if (source === 'ec2' || source === 'custom' || source === 'vmware' || source === 'openstack' || source === 'scm' || source === 'cloudforms' || source === "satellite6" || source === "azure_rm") {
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

            // reset fields
            $scope.group_by_choices = source === 'ec2' ? $scope.ec2_group_by : null;
            // azure_rm regions choices are keyed as "azure" in an OPTIONS request to the inventory_sources endpoint
            $scope.source_region_choices = source === 'azure_rm' ? $scope.azure_regions : $scope[source + '_regions'];
            $scope.cloudCredentialRequired = source !== '' && source !== 'scm' && source !== 'custom' && source !== 'ec2' ? true : false;
            $scope.source_regions = null;
            $scope.credential = null;
            $scope.credential_name = null;
            $scope.group_by = null;
            $scope.group_by_choices = [];
            $scope.overwrite_vars = false;
            initRegionSelect();
        };
        // region / source options callback

        $scope.$on('sourceTypeOptionsReady', function() {
            CreateSelect2({
                element: '#inventory_source_source',
                multiple: false
            });
        });

        function initRegionSelect(){
            CreateSelect2({
                element: '#inventory_source_source_regions',
                multiple: true
            });

            let add_new = false;
            if( _.get($scope, 'source') === 'ec2' || _.get($scope.source, 'value') === 'ec2') {
                $scope.group_by_choices = $scope.ec2_group_by;
                $scope.groupByPopOver = "<p>" + i18n._("Select which groups to create automatically. ") +
                $rootScope.BRAND_NAME + i18n._(" will create group names similar to the following examples based on the options selected:") + "</p><ul>" +
                "<li>" + i18n._("Availability Zone:") + "<strong>zones &raquo; us-east-1b</strong></li>" +
                "<li>" + i18n._("Image ID:") + "<strong>images &raquo; ami-b007ab1e</strong></li>" +
                "<li>" + i18n._("Instance ID:") + "<strong>instances &raquo; i-ca11ab1e</strong></li>" +
                "<li>" + i18n._("Instance Type:") + "<strong>types &raquo; type_m1_medium</strong></li>" +
                "<li>" + i18n._("Key Name:") + "<strong>keys &raquo; key_testing</strong></li>" +
                "<li>" + i18n._("Region:") + "<strong>regions &raquo; us-east-1</strong></li>" +
                "<li>" + i18n._("Security Group:") + "<strong>security_groups &raquo; security_group_default</strong></li>" +
                "<li>" + i18n._("Tags:") + "<strong>tags &raquo; tag_Name &raquo; tag_Name_host1</strong></li>" +
                "<li>" + i18n._("VPC ID:") + "<strong>vpcs &raquo; vpc-5ca1ab1e</strong></li>" +
                "<li>" + i18n._("Tag None:") + "<strong>tags &raquo; tag_none</strong></li>" +
                "</ul><p>" + i18n._("If blank, all groups above are created except") + "<em>" + i18n._("Instance ID") + "</em>.</p>";

                $scope.instanceFilterPopOver = "<p>" + i18n._("Provide a comma-separated list of filter expressions. ") +
                i18n._("Hosts are imported to ") + $rootScope.BRAND_NAME + i18n._(" when ") + "<em>" + i18n._("ANY") + "</em>" + i18n._(" of the filters match.") + "</p>" +
                i18n._("Limit to hosts having a tag:") + "<br />\n" +
                "<blockquote>tag-key=TowerManaged</blockquote>\n" +
                i18n._("Limit to hosts using either key pair:") + "<br />\n" +
                "<blockquote>key-name=staging, key-name=production</blockquote>\n" +
                i18n._("Limit to hosts where the Name tag begins with ") + "<em>" + i18n._("test") + "</em>:<br />\n" +
                "<blockquote>tag:Name=test*</blockquote>\n" +
                "<p>" + i18n._("View the ") + "<a href=\"http://docs.aws.amazon.com/AWSEC2/latest/APIReference/ApiReference-query-DescribeInstances.html\" target=\"_blank\">" + i18n._("Describe Instances documentation") + "</a> " +
                i18n._("for a complete list of supported filters.") + "</p>";
            }
            if( _.get($scope, 'source') === 'vmware' || _.get($scope.source, 'value') === 'vmware') {
                add_new = true;
                $scope.group_by_choices = [];
                $scope.group_by = $scope.group_by_choices;
                $scope.groupByPopOver = i18n._("Specify which groups to create automatically. Group names will be created similar to the options selected. If blank, all groups above are created. Refer to Ansible Tower documentation for more detail.");
                $scope.instanceFilterPopOver = i18n._("Provide a comma-separated list of filter expressions. Hosts are imported when all of the filters match. Refer to Ansible Tower documentation for more detail.");
            }
            if( _.get($scope, 'source') === 'tower' || _.get($scope.source, 'value') === 'tower') {
                $scope.instanceFilterPopOver = i18n._("Provide the named URL encoded name or id of the remote Tower inventory to be imported.");
            }
            CreateSelect2({
                element: '#inventory_source_group_by',
                multiple: true,
                addNew: add_new
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
                custom_virtualenv: $scope.custom_virtualenv || null,
                // comma-delimited strings
                group_by: SourcesService.encodeGroupBy($scope.source, $scope.group_by),
                source_regions: _.map($scope.source_regions, 'value').join(','),
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
