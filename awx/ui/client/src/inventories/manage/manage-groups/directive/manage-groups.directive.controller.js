/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

function manageGroupsDirectiveController($filter, $location, $log,
    $stateParams, $compile, $state, $scope, Rest, Alert, GroupForm,
    GenerateForm, Prompt, ProcessErrors, GetBasePath, SetNodeName,
    ParseTypeChange, GetSourceTypeOptions, InventoryUpdate, LookUpInit, Empty,
    Wait, GetChoices, UpdateGroup, SourceChange, Find, ParseVariableString,
    ToJSON, GroupsScheduleListInit, SetSchedulesInnerDialogSize,
    CreateSelect2, ToggleNotification, NotificationsListInit,
    RelatedSearchInit, RelatedPaginateInit) {

    var vm = this;

    var group_id = $stateParams.group_id,
        mode = $state.current.data.mode,
        inventory_id = $stateParams.inventory_id,
        generator = GenerateForm,
        group_created = false,
        defaultUrl,
        master = {},
        form = GroupForm(),
        relatedSets = {},
        choicesReady, group;

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
            for (var fld in form.fields) {
                if (data[fld]) {
                    $scope[fld] = data[fld];
                    master[fld] = $scope[fld];
                }
            }
            if(mode === 'edit') {
                // schedules_url = data.related.inventory_source + 'schedules/';
                $scope.variable_url = data.related.variable_data;
                $scope.source_url = data.related.inventory_source;
                $scope.source_id = $scope.source_url.split('/')[4];
                $scope.$emit('LoadSourceData');
            }
        })
        .error(function(data, status) {
            ProcessErrors($scope, data, status, {
                hdr: 'Error!',
                msg: 'Failed to retrieve group: ' + defaultUrl + '. GET status: ' + status
            });
        });


    $scope.parseType = 'yaml';

    generator.inject(form, {
        mode: mode,
        id: 'group-manage-panel',
        tabs: true,
        scope: $scope
    });

    generator.reset();

    GetSourceTypeOptions({
        scope: $scope,
        variable: 'source_type_options'
    });


    $scope.source = form.fields.source['default'];
    $scope.sourcePathRequired = false;
    $scope[form.fields.source_vars.parseTypeName] = 'yaml';
    $scope.update_cache_timeout = 0;
    $scope.parseType = 'yaml';

    function initSourceChange() {
        $scope.showSchedulesTab = (mode === 'edit' && $scope.source && $scope.source.value !== "manual") ? true : false;
        SourceChange({
            scope: $scope,
            form: form
        });
    }

    // JT -- this gets called after the properties & properties variables are loaded, and is emitted from (groupLoaded)
    if ($scope.removeLoadSourceData) {
        $scope.removeLoadSourceData();
    }
    $scope.removeLoadSourceData = $scope.$on('LoadSourceData', function() {
        ParseTypeChange({
            scope: $scope,
            variable: 'variables',
            parse_variable: 'parseType',
            field_id: 'group_variables'
        });

        NotificationsListInit({
            scope: $scope,
            url: GetBasePath('inventory_sources'),
            id: $scope.source_id
        });

        if ($scope.source_url) {
            // get source data
            Rest.setUrl($scope.source_url);
            Rest.get()
                .success(function(data) {
                    var fld, i, j, flag, found, set, opts, list;
                    for (fld in form.fields) {
                        if (fld === 'checkbox_group') {
                            for (i = 0; i < form.fields[fld].fields.length; i++) {
                                flag = form.fields[fld].fields[i];
                                if (data[flag.name] !== undefined) {
                                    $scope[flag.name] = data[flag.name];
                                    master[flag.name] = $scope[flag.name];
                                }
                            }
                        }
                        if (fld === 'source') {
                            found = false;
                            data.source = (data.source === "") ? "manual" : data.source;
                            for (i = 0; i < $scope.source_type_options.length; i++) {
                                if ($scope.source_type_options[i].value === data.source) {
                                    $scope.source = $scope.source_type_options[i];
                                    found = true;
                                }
                            }
                            if (!found || $scope.source.value === "manual") {
                                $scope.groupUpdateHide = true;
                            } else {
                                $scope.groupUpdateHide = false;
                            }
                            master.source = $scope.source;
                        } else if (fld === 'source_vars') {
                            // Parse source_vars, converting to YAML.
                            $scope.source_vars = ParseVariableString(data.source_vars);
                            master.source_vars = $scope.variables;
                        } else if (fld === "inventory_script") {
                            // the API stores it as 'source_script', we call it inventory_script
                            data.summary_fields['inventory_script'] = data.summary_fields.source_script;
                            $scope.inventory_script = data.source_script;
                            master.inventory_script = $scope.inventory_script;
                        } else if (fld === "source_regions") {
                            if (data[fld] === "") {
                                $scope[fld] = data[fld];
                                master[fld] = $scope[fld];
                            } else {
                                $scope[fld] = data[fld].split(",");
                                master[fld] = $scope[fld];
                            }
                        } else if (data[fld] !== undefined &&
                            fld !== "description" &&
                            fld !== "name" &&
                            fld !== "variables") {
                            $scope[fld] = data[fld];
                            master[fld] = $scope[fld];
                        }

                        if (form.fields[fld].sourceModel && data.summary_fields &&
                            data.summary_fields[form.fields[fld].sourceModel]) {
                            $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                            master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                        }
                    }
                    relatedSets = form.relatedSets(data.related);
                    RelatedSearchInit({
                        scope: $scope,
                        form: form,
                        relatedSets: relatedSets
                    });

                    RelatedPaginateInit({
                        scope: $scope,
                        relatedSets: relatedSets
                    });
                    initSourceChange();

                    if (data.source_regions) {
                        if (data.source === 'ec2' ||
                            data.source === 'rax' ||
                            data.source === 'gce' ||
                            data.source === 'azure') {
                            if (data.source === 'ec2') {
                                set = $scope.ec2_regions;
                            } else if (data.source === 'rax') {
                                set = $scope.rax_regions;
                            } else if (data.source === 'gce') {
                                set = $scope.gce_regions;
                            } else if (data.source === 'azure') {
                                set = $scope.azure_regions;
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
                                element: "group_source_regions",
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
                        set = $scope.ec2_group_by;
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

                    $scope.group_update_url = data.related.update;
                    for (set in relatedSets) {
                        $scope.search(relatedSets[set].iterator);
                    }
                })
                .error(function(data, status) {
                    $scope.source = "";
                    ProcessErrors($scope, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to retrieve inventory source. GET status: ' + status
                    });
                });
        }
    });

    if ($scope.remove$scopeSourceTypeOptionsReady) {
        $scope.remove$scopeSourceTypeOptionsReady();
    }
    $scope.remove$scopeSourceTypeOptionsReady = $scope.$on('sourceTypeOptionsReady', function() {
        if (mode === 'add') {
            $scope.source = Find({
                list: $scope.source_type_options,
                key: 'value',
                val: ''
            });
            $scope.showSchedulesTab = false;
        }
    });

    choicesReady = 0;

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReadyGroup', function() {
        CreateSelect2({
            element: '#group_source',
            multiple: false
        });
        $scope.$emit('LoadSourceData');

        choicesReady++;
        if (choicesReady === 5) {
            if (mode !== 'edit') {
                $scope.variables = "---";
                master.variables = $scope.variables;
            }
        }
    });

    // Load options for source regions
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

    //Wait('start');

    if ($scope.removeAddTreeRefreshed) {
        $scope.removeAddTreeRefreshed();
    }
    $scope.removeAddTreeRefreshed = $scope.$on('GroupTreeRefreshed', function() {
        // Clean up
        Wait('stop');

        if ($scope.searchCleanUp) {
            $scope.searchCleanup();
        }
        try {
            //$('#group-modal-dialog').dialog('close');
        } catch (e) {
            // ignore
        }
    });

    if ($scope.removeSaveComplete) {
        $scope.removeSaveComplete();
    }
    $scope.removeSaveComplete = $scope.$on('SaveComplete', function(e, error) {
        if (!error) {
            $scope.formCancel();
        }
    });

    if ($scope.removeFormSaveSuccess) {
        $scope.removeFormSaveSuccess();
    }
    $scope.removeFormSaveSuccess = $scope.$on('formSaveSuccess', function() {

        // Source data gets stored separately from the group. Validate and store Source
        // related fields, then call SaveComplete to wrap things up.

        var parseError = false,
            regions, r, i,
            group_by,
            data = {
                group: group_id,
                source: (($scope.source && $scope.source.value !== 'manual') ? $scope.source.value : ''),
                source_path: $scope.source_path,
                credential: $scope.credential,
                overwrite: $scope.overwrite,
                overwrite_vars: $scope.overwrite_vars,
                source_script: $scope.inventory_script,
                update_on_launch: $scope.update_on_launch,
                update_cache_timeout: ($scope.update_cache_timeout || 0)
            };

        // Create a string out of selected list of regions
        if ($scope.source_regions) {
            regions = $('#group_source_regions').select2("data");
            r = [];
            for (i = 0; i < regions.length; i++) {
                r.push(regions[i].id);
            }
            data.source_regions = r.join();
        }

        if ($scope.source && ($scope.source.value === 'ec2')) {
            data.instance_filters = $scope.instance_filters;
            // Create a string out of selected list of regions
            group_by = $('#source_group_by').select2("data");
            r = [];
            for (i = 0; i < group_by.length; i++) {
                r.push(group_by[i].id);
            }
            data.group_by = r.join();
        }

        if ($scope.source && ($scope.source.value === 'ec2')) {
            // for ec2, validate variable data
            data.source_vars = ToJSON($scope.envParseType, $scope.source_vars, true);
        }

        if ($scope.source && ($scope.source.value === 'custom')) {
            data.source_vars = ToJSON($scope.envParseType, $scope.extra_vars, true);
        }

        if ($scope.source && ($scope.source.value === 'vmware' ||
                $scope.source.value === 'openstack')) {
            data.source_vars = ToJSON($scope.envParseType, $scope.inventory_variables, true);
        }

        // the API doesn't expect the credential to be passed with a custom inv script
        if ($scope.source && $scope.source.value === 'custom') {
            delete(data.credential);
        }

        if (!parseError) {
            Rest.setUrl($scope.source_url);
            Rest.put(data)
                .success(function() {
                    $scope.$emit('SaveComplete', false);
                })
                .error(function(data, status) {
                    $('#group_tabs a:eq(1)').tab('show');
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to update group inventory source. PUT status: ' + status
                    });
                });
        }
    });
    $scope.toggleNotification = function(event, notifier_id, column) {
        var notifier = this.notification;
        try {
            $(event.target).tooltip('hide');
        }
        catch(e) {
            // ignore
        }
        ToggleNotification({
            scope: $scope,
            url: GetBasePath('inventory_sources'),
            id: $scope.source_id,
            notifier: notifier,
            column: column,
            callback: 'NotificationRefresh'
        });
    };
    // Cancel
    $scope.formCancel = function() {
        Wait('stop');
        $state.go('inventoryManage', {}, {reload: true});
    };

    // Save
    $scope.saveGroup = function() {
        Wait('start');
        var fld, data, json_data;

        try {

            json_data = ToJSON($scope.parseType, $scope.variables, true);

            data = {};
            for (fld in form.fields) {
                data[fld] = $scope[fld];
            }

            data.inventory = inventory_id;

            Rest.setUrl(defaultUrl);
            if (mode === 'edit' || (mode === 'add' && group_created)) {
                Rest.put(data)
                    .success(function() {
                        $scope.$emit('formSaveSuccess');
                    })
                    .error(function(data, status) {
                        $('#group_tabs a:eq(0)').tab('show');
                        ProcessErrors($scope, data, status, form, {
                            hdr: 'Error!',
                            msg: 'Failed to update group: ' + group_id + '. PUT status: ' + status
                        });
                    });
            } else {
                Rest.post(data)
                    .success(function(data) {
                        group_created = true;
                        group_id = data.id;
                        $scope.source_url = data.related.inventory_source;
                        $scope.source_id = $scope.source_url.split('/')[4];
                        $scope.$emit('formSaveSuccess');
                    })
                    .error(function(data, status) {
                        $('#group_tabs a:eq(0)').tab('show');
                        ProcessErrors($scope, data, status, form, {
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
    $scope.updateGroup = function() {
        if ($scope.source === "manual" || $scope.source === null) {
            Alert('Missing Configuration', 'The selected group is not configured for updates. You must first edit the group, provide Source settings, ' +
                'and then run an update.', 'alert-info');
        } else if ($scope.status === 'updating') {
            Alert('Update in Progress', 'The inventory update process is currently running for group <em>' +
                $filter('sanitize')($scope.summary_fields.group.name) + '</em>. Use the Refresh button to monitor the status.', 'alert-info', null, null, null, null, true);
        } else {
            InventoryUpdate({
                scope: $scope,
                group_id: group_id,
                url: $scope.group_update_url,
                group_name: $scope.name,
                group_source: $scope.source.value
            });
        }
    };

    // Change the lookup and regions when the source changes
    $scope.sourceChange = function() {
        $scope.credential_name = "";
        $scope.credential = "";
        if ($scope.credential_name_api_error) {
            delete $scope.credential_name_api_error;
        }
        initSourceChange();
    };


    angular.extend(vm, {
        formCancel : $scope.formCancel,
        saveGroup: $scope.saveGroup
    });
}

export default ['$filter', '$location', '$log', '$stateParams',
    '$compile', '$state', '$scope', 'Rest', 'Alert', 'GroupForm',
    'GenerateForm','Prompt', 'ProcessErrors', 'GetBasePath', 'SetNodeName',
    'ParseTypeChange', 'GetSourceTypeOptions', 'InventoryUpdate', 'LookUpInit',
    'Empty', 'Wait', 'GetChoices', 'UpdateGroup', 'SourceChange', 'Find',
    'ParseVariableString', 'ToJSON', 'GroupsScheduleListInit',
    'SetSchedulesInnerDialogSize', 'CreateSelect2',
    'ToggleNotification', 'NotificationsListInit', 'RelatedSearchInit',
    'RelatedPaginateInit',
    manageGroupsDirectiveController
];
