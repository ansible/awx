/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

function manageGroupsDirectiveController($filter, $rootScope, $location, $log, $stateParams, $compile, $state, $scope, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
    GetBasePath, SetNodeName, ParseTypeChange, GetSourceTypeOptions, InventoryUpdate, LookUpInit, Empty, Wait,
    GetChoices, UpdateGroup, SourceChange, Find, ParseVariableString, ToJSON, GroupsScheduleListInit,
    SourceForm, SetSchedulesInnerDialogSize, CreateSelect2, ParamPass) {

    var vm = this;
    var params = ParamPass.get();
    if(params === undefined) {
        params = {};
        params.scope = $scope.$new();
    }
    var parent_scope = params.scope,
        group_id = $stateParams.group_id,
        mode = $state.current.data.mode, // 'add' or 'edit'
        inventory_id = $stateParams.inventory_id,
        generator = GenerateForm,
        group_created = false,
        defaultUrl,
        master = {},
        choicesReady,
        modal_scope = parent_scope.$new(),
        properties_scope = parent_scope.$new(),
        sources_scope = parent_scope.$new(),
        elem, group,
        schedules_url = '';

    if (mode === 'edit') {
        defaultUrl = GetBasePath('groups') + group_id + '/';
    } else {
        defaultUrl = (group_id !== undefined) ? GetBasePath('groups') + group_id + '/children/' :
            GetBasePath('inventory') + inventory_id + '/groups/';
    }

    Rest.setUrl(defaultUrl);
    Rest.get()
        .success(function(data) {
            group = data;
            for (var fld in GroupForm.fields) {
                if (data[fld]) {
                    properties_scope[fld] = data[fld];
                    master[fld] = properties_scope[fld];
                }
            }
            if(mode === 'edit') {
                schedules_url = data.related.inventory_source + 'schedules/';
                properties_scope.variable_url = data.related.variable_data;
                sources_scope.source_url = data.related.inventory_source;
                modal_scope.$emit('LoadSourceData');
            }
        })
        .error(function(data, status) {
            ProcessErrors(modal_scope, data, status, {
                hdr: 'Error!',
                msg: 'Failed to retrieve group: ' + defaultUrl + '. GET status: ' + status
            });
        });


    $('#properties-tab').empty();
    $('#sources-tab').empty();

    elem = document.getElementById('group-manage-panel');
    $compile(elem)(modal_scope);

    $scope.parseType = 'yaml';

    var form_scope =
        generator.inject(GroupForm, {
            mode: mode,
            id: 'properties-tab',
            related: false,
            scope: properties_scope,
            cancelButton: false,
        });
    var source_form_scope =
        generator.inject(SourceForm, {
            mode: mode,
            id: 'sources-tab',
            related: false,
            scope: sources_scope,
            cancelButton: false
        });

    generator.reset();

    GetSourceTypeOptions({
        scope: sources_scope,
        variable: 'source_type_options'
    });
    sources_scope.source = SourceForm.fields.source['default'];
    sources_scope.sourcePathRequired = false;
    sources_scope[SourceForm.fields.source_vars.parseTypeName] = 'yaml';
    sources_scope.update_cache_timeout = 0;
    properties_scope.parseType = 'yaml';

    function waitStop() {
        Wait('stop');
    }

    function initSourceChange() {
        parent_scope.showSchedulesTab = (mode === 'edit' && sources_scope.source && sources_scope.source.value !== "manual") ? true : false;
        SourceChange({
            scope: sources_scope,
            form: SourceForm
        });
    }

    // JT -- this gets called after the properties & properties variables are loaded, and is emitted from (groupLoaded)
    if (modal_scope.removeLoadSourceData) {
        modal_scope.removeLoadSourceData();
    }
    modal_scope.removeLoadSourceData = modal_scope.$on('LoadSourceData', function() {
        ParseTypeChange({
            scope: form_scope,
            variable: 'variables',
            parse_variable: 'parseType',
            field_id: 'group_variables'
        });

        if (sources_scope.source_url) {
            // get source data
            Rest.setUrl(sources_scope.source_url);
            Rest.get()
                .success(function(data) {
                    var fld, i, j, flag, found, set, opts, list, form;
                    form = SourceForm;
                    for (fld in form.fields) {
                        if (fld === 'checkbox_group') {
                            for (i = 0; i < form.fields[fld].fields.length; i++) {
                                flag = form.fields[fld].fields[i];
                                if (data[flag.name] !== undefined) {
                                    sources_scope[flag.name] = data[flag.name];
                                    master[flag.name] = sources_scope[flag.name];
                                }
                            }
                        }
                        if (fld === 'source') {
                            found = false;
                            data.source = (data.source === "") ? "manual" : data.source;
                            for (i = 0; i < sources_scope.source_type_options.length; i++) {
                                if (sources_scope.source_type_options[i].value === data.source) {
                                    sources_scope.source = sources_scope.source_type_options[i];
                                    found = true;
                                }
                            }
                            if (!found || sources_scope.source.value === "manual") {
                                sources_scope.groupUpdateHide = true;
                            } else {
                                sources_scope.groupUpdateHide = false;
                            }
                            master.source = sources_scope.source;
                        } else if (fld === 'source_vars') {
                            // Parse source_vars, converting to YAML.
                            sources_scope.source_vars = ParseVariableString(data.source_vars);
                            master.source_vars = sources_scope.variables;
                        } else if (fld === "inventory_script") {
                            // the API stores it as 'source_script', we call it inventory_script
                            data.summary_fields['inventory_script'] = data.summary_fields.source_script;
                            sources_scope.inventory_script = data.source_script;
                            master.inventory_script = sources_scope.inventory_script;
                        } else if (fld === "source_regions") {
                            if (data[fld] === "") {
                                sources_scope[fld] = data[fld];
                                master[fld] = sources_scope[fld];
                            } else {
                                sources_scope[fld] = data[fld].split(",");
                                master[fld] = sources_scope[fld];
                            }
                        } else if (data[fld] !== undefined) {
                            sources_scope[fld] = data[fld];
                            master[fld] = sources_scope[fld];
                        }

                        if (form.fields[fld].sourceModel && data.summary_fields &&
                            data.summary_fields[form.fields[fld].sourceModel]) {
                            sources_scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                            master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                        }
                    }

                    initSourceChange();

                    if (data.source_regions) {
                        if (data.source === 'ec2' ||
                            data.source === 'rax' ||
                            data.source === 'gce' ||
                            data.source === 'azure') {
                            if (data.source === 'ec2') {
                                set = sources_scope.ec2_regions;
                            } else if (data.source === 'rax') {
                                set = sources_scope.rax_regions;
                            } else if (data.source === 'gce') {
                                set = sources_scope.gce_regions;
                            } else if (data.source === 'azure') {
                                set = sources_scope.azure_regions;
                            }
                            opts = [];
                            list = data.source_regions.split(',');
                            for (i = 0; i < list.length; i++) {
                                for (j = 0; j < set.length; j++) {
                                    if (list[i] === set[j].value) {
                                        opts.push({
                                            id: set [j].value,
                                            text: set [j].label
                                        });
                                    }
                                }
                            }
                            master.source_regions = opts;
                            CreateSelect2({
                                element: "#source_source_regions",
                                opts: opts
                            });

                        }
                    } else {
                        // If empty, default to all
                        master.source_regions = [{
                            id: 'all',
                            text: 'All'
                        }];
                    }
                    if (data.group_by && data.source === 'ec2') {
                        set = sources_scope.ec2_group_by;
                        opts = [];
                        list = data.group_by.split(',');
                        for (i = 0; i < list.length; i++) {
                            for (j = 0; j < set.length; j++) {
                                if (list[i] === set[j].value) {
                                    opts.push({
                                        id: set [j].value,
                                        text: set [j].label
                                    });
                                }
                            }
                        }
                        master.group_by = opts;
                        CreateSelect2({
                            element: "#source_group_by",
                            opts: opts
                        });
                    }

                    sources_scope.group_update_url = data.related.update;
                })
                .error(function(data, status) {
                    sources_scope.source = "";
                    ProcessErrors(modal_scope, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to retrieve inventory source. GET status: ' + status
                    });
                });
        }
    });

    if (sources_scope.removeScopeSourceTypeOptionsReady) {
        sources_scope.removeScopeSourceTypeOptionsReady();
    }
    sources_scope.removeScopeSourceTypeOptionsReady = sources_scope.$on('sourceTypeOptionsReady', function() {
        if (mode === 'add') {
            sources_scope.source = Find({
                list: sources_scope.source_type_options,
                key: 'value',
                val: ''
            });
            modal_scope.showSchedulesTab = false;
        }
    });

    choicesReady = 0;

    if (sources_scope.removeChoicesReady) {
        sources_scope.removeChoicesReady();
    }
    sources_scope.removeChoicesReady = sources_scope.$on('choicesReadyGroup', function() {
        CreateSelect2({
            element: '#source_source',
            multiple: false
        });
        modal_scope.$emit('LoadSourceData');

        choicesReady++;
        if (choicesReady === 5) {
            if (mode !== 'edit') {
                properties_scope.variables = "---";
                master.variables = properties_scope.variables;
            }
        }
    });

    // Load options for source regions
    GetChoices({
        scope: sources_scope,
        url: GetBasePath('inventory_sources'),
        field: 'source_regions',
        variable: 'rax_regions',
        choice_name: 'rax_region_choices',
        callback: 'choicesReadyGroup'
    });

    GetChoices({
        scope: sources_scope,
        url: GetBasePath('inventory_sources'),
        field: 'source_regions',
        variable: 'ec2_regions',
        choice_name: 'ec2_region_choices',
        callback: 'choicesReadyGroup'
    });

    GetChoices({
        scope: sources_scope,
        url: GetBasePath('inventory_sources'),
        field: 'source_regions',
        variable: 'gce_regions',
        choice_name: 'gce_region_choices',
        callback: 'choicesReadyGroup'
    });

    GetChoices({
        scope: sources_scope,
        url: GetBasePath('inventory_sources'),
        field: 'source_regions',
        variable: 'azure_regions',
        choice_name: 'azure_region_choices',
        callback: 'choicesReadyGroup'
    });

    // Load options for group_by
    GetChoices({
        scope: sources_scope,
        url: GetBasePath('inventory_sources'),
        field: 'group_by',
        variable: 'ec2_group_by',
        choice_name: 'ec2_group_by_choices',
        callback: 'choicesReadyGroup'
    });

    //Wait('start');

    if (parent_scope.removeAddTreeRefreshed) {
        parent_scope.removeAddTreeRefreshed();
    }
    parent_scope.removeAddTreeRefreshed = parent_scope.$on('GroupTreeRefreshed', function() {
        // Clean up
        Wait('stop');

        if (modal_scope.searchCleanUp) {
            modal_scope.searchCleanup();
        }
        try {
            //$('#group-modal-dialog').dialog('close');
        } catch (e) {
            // ignore
        }
    });

    if (modal_scope.removeSaveComplete) {
        modal_scope.removeSaveComplete();
    }
    modal_scope.removeSaveComplete = modal_scope.$on('SaveComplete', function(e, error) {
        if (!error) {
            modal_scope.cancelPanel();
        }
    });

    if (modal_scope.removeFormSaveSuccess) {
        modal_scope.removeFormSaveSuccess();
    }
    modal_scope.removeFormSaveSuccess = modal_scope.$on('formSaveSuccess', function() {

        // Source data gets stored separately from the group. Validate and store Source
        // related fields, then call SaveComplete to wrap things up.

        var parseError = false,
            regions, r, i,
            group_by,
            data = {
                group: group_id,
                source: ((sources_scope.source && sources_scope.source.value !== 'manual') ? sources_scope.source.value : ''),
                source_path: sources_scope.source_path,
                credential: sources_scope.credential,
                overwrite: sources_scope.overwrite,
                overwrite_vars: sources_scope.overwrite_vars,
                source_script: sources_scope.inventory_script,
                update_on_launch: sources_scope.update_on_launch,
                update_cache_timeout: (sources_scope.update_cache_timeout || 0)
            };

        // Create a string out of selected list of regions
        if (sources_scope.source_regions) {
            regions = $('#source_source_regions').select2("data");
            r = [];
            for (i = 0; i < regions.length; i++) {
                r.push(regions[i].id);
            }
            data.source_regions = r.join();
        }

        if (sources_scope.source && (sources_scope.source.value === 'ec2')) {
            data.instance_filters = sources_scope.instance_filters;
            // Create a string out of selected list of regions
            group_by = $('#source_group_by').select2("data");
            r = [];
            for (i = 0; i < group_by.length; i++) {
                r.push(group_by[i].id);
            }
            data.group_by = r.join();
        }

        if (sources_scope.source && (sources_scope.source.value === 'ec2')) {
            // for ec2, validate variable data
            data.source_vars = ToJSON(sources_scope.envParseType, sources_scope.source_vars, true);
        }

        if (sources_scope.source && (sources_scope.source.value === 'custom')) {
            data.source_vars = ToJSON(sources_scope.envParseType, sources_scope.extra_vars, true);
        }

        if (sources_scope.source && (sources_scope.source.value === 'vmware' ||
                sources_scope.source.value === 'openstack')) {
            data.source_vars = ToJSON(sources_scope.envParseType, sources_scope.inventory_variables, true);
        }

        // the API doesn't expect the credential to be passed with a custom inv script
        if (sources_scope.source && sources_scope.source.value === 'custom') {
            delete(data.credential);
        }

        if (!parseError) {
            Rest.setUrl(sources_scope.source_url);
            Rest.put(data)
                .success(function() {
                    modal_scope.$emit('SaveComplete', false);
                })
                .error(function(data, status) {
                    $('#group_tabs a:eq(1)').tab('show');
                    ProcessErrors(sources_scope, data, status, SourceForm, {
                        hdr: 'Error!',
                        msg: 'Failed to update group inventory source. PUT status: ' + status
                    });
                });
        }
    });

    // Cancel
    modal_scope.cancelPanel = function() {
        Wait('stop');
        $state.go('inventoryManage', {}, {reload: true});
    };

    // Save
    modal_scope.saveGroup = function() {
        Wait('start');
        var fld, data, json_data;

        try {

            json_data = ToJSON(properties_scope.parseType, properties_scope.variables, true);

            data = {};
            for (fld in GroupForm.fields) {
                data[fld] = properties_scope[fld];
            }

            data.inventory = inventory_id;

            Rest.setUrl(defaultUrl);
            if (mode === 'edit' || (mode === 'add' && group_created)) {
                Rest.put(data)
                    .success(function() {
                        modal_scope.$emit('formSaveSuccess');
                    })
                    .error(function(data, status) {
                        $('#group_tabs a:eq(0)').tab('show');
                        ProcessErrors(properties_scope, data, status, GroupForm, {
                            hdr: 'Error!',
                            msg: 'Failed to update group: ' + group_id + '. PUT status: ' + status
                        });
                    });
            } else {
                Rest.post(data)
                    .success(function(data) {
                        group_created = true;
                        group_id = data.id;
                        sources_scope.source_url = data.related.inventory_source;
                        modal_scope.$emit('formSaveSuccess');
                    })
                    .error(function(data, status) {
                        $('#group_tabs a:eq(0)').tab('show');
                        ProcessErrors(properties_scope, data, status, GroupForm, {
                            hdr: 'Error!',
                            msg: 'Failed to create group: ' + group_id + '. POST status: ' + status
                        });
                    });
            }
        } catch (e) {
            // ignore. ToJSON will have already alerted the user
        }
    };

    // Start the update process
    modal_scope.updateGroup = function() {
        if (sources_scope.source === "manual" || sources_scope.source === null) {
            Alert('Missing Configuration', 'The selected group is not configured for updates. You must first edit the group, provide Source settings, ' +
                'and then run an update.', 'alert-info');
        } else if (sources_scope.status === 'updating') {
            Alert('Update in Progress', 'The inventory update process is currently running for group <em>' +
                $filter('sanitize')(sources_scope.summary_fields.group.name) + '</em>. Use the Refresh button to monitor the status.', 'alert-info', null, null, null, null, true);
        } else {
            InventoryUpdate({
                scope: parent_scope,
                group_id: group_id,
                url: properties_scope.group_update_url,
                group_name: properties_scope.name,
                group_source: sources_scope.source.value
            });
        }
    };

    // Change the lookup and regions when the source changes
    sources_scope.sourceChange = function() {
        sources_scope.credential_name = "";
        sources_scope.credential = "";
        if (sources_scope.credential_name_api_error) {
            delete sources_scope.credential_name_api_error;
        }
        initSourceChange();
    };


    angular.extend(vm, {
        cancelPanel : modal_scope.cancelPanel,
        saveGroup: modal_scope.saveGroup
    });
}

export default ['$filter', '$rootScope', '$location', '$log', '$stateParams', '$compile', '$state', '$scope', 'Rest', 'Alert', 'GroupForm', 'GenerateForm',
    'Prompt', 'ProcessErrors', 'GetBasePath', 'SetNodeName', 'ParseTypeChange', 'GetSourceTypeOptions', 'InventoryUpdate',
    'LookUpInit', 'Empty', 'Wait', 'GetChoices', 'UpdateGroup', 'SourceChange', 'Find',
    'ParseVariableString', 'ToJSON', 'GroupsScheduleListInit', 'SourceForm', 'SetSchedulesInnerDialogSize', 'CreateSelect2', 'ParamPass',
    manageGroupsDirectiveController
];
