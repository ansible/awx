/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  GroupsHelper
 *
 *  Routines that handle group add/edit/delete on the Inventory tree widget.
 *
 */
 
'use strict';

angular.module('GroupsHelper', ['RestServices', 'Utilities', 'ListGenerator', 'GroupListDefinition', 'SearchHelper',
    'PaginationHelpers', 'ListGenerator', 'AuthService', 'GroupsHelper', 'InventoryHelper', 'SelectionHelper',
    'JobSubmissionHelper', 'RefreshHelper', 'PromptDialog', 'CredentialsListDefinition', 'InventoryTree',
    'InventoryStatusDefinition', 'VariablesHelper', 'SchedulesListDefinition', 'SourceFormDefinition'])

.factory('GetSourceTypeOptions', ['Rest', 'ProcessErrors', 'GetBasePath',
    function (Rest, ProcessErrors, GetBasePath) {
        return function (params) {
            // Lookup options for source and build an array of drop-down choices
            var scope = params.scope,
                variable = params.variable;
            if (scope[variable] === undefined) {
                scope[variable] = [];
                Rest.setUrl(GetBasePath('inventory_sources'));
                Rest.options()
                    .success(function (data) {
                        var i, choices = data.actions.GET.source.choices;
                        for (i = 0; i < choices.length; i++) {
                            if (choices[i][0] !== 'file') {
                                scope[variable].push({
                                    label: ((choices[i][0] === '') ? 'Manual' : choices[i][1]),
                                    value: choices[i][0]
                                });
                            }
                        }
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to retrieve options for inventory_sources.source. OPTIONS status: ' + status
                        });
                    });
            }
        };
    }
])


.factory('ViewUpdateStatus', ['Rest', 'ProcessErrors', 'GetBasePath', 'ShowUpdateStatus', 'Alert', 'Wait', 'Empty', 'Find',
    function (Rest, ProcessErrors, GetBasePath, ShowUpdateStatus, Alert, Wait, Empty, Find) {
        return function (params) {

            var scope = params.scope,
                tree_id = params.tree_id,
                group_id = params.group_id,
                group = Find({ list: scope.groups, key: 'id', val: tree_id });

            if (group) {
                if (Empty(group.source)) {
                    Alert('Missing Configuration', 'The selected group is not configured for inventory sync. ' +
                        'You must first edit the group, provide Source settings, and then run the sync process.', 'alert-info');
                } else if (Empty(group.status) || group.status === "never updated") {
                    Alert('No Status Available', 'An inventory sync has not been performed for the selected group. Start the process by ' +
                        'clicking the <i class="fa fa-exchange"></i> button.', 'alert-info');
                } else {
                    Wait('start');
                    Rest.setUrl(group.related.inventory_source);
                    Rest.get()
                        .success(function (data) {
                            var url = (data.related.current_update) ? data.related.current_update : data.related.last_update;
                            ShowUpdateStatus({
                                group_name: data.summary_fields.group.name,
                                last_update: url,
                                license_error: ((data.summary_fields.last_update && data.summary_fields.last_update.license_error) ? true : false),
                                tree_id: tree_id,
                                group_id: group_id,
                                parent_scope: scope
                            });
                        })
                        .error(function (data, status) {
                            Wait('stop');
                            ProcessErrors(scope, data, status, null, {
                                hdr: 'Error!',
                                msg: 'Failed to retrieve inventory source: ' + group.related.inventory_source +
                                    ' POST returned status: ' + status
                            });
                        });
                }
            }

        };
    }
])

.factory('GetHostsStatusMsg', [
    function () {
        return function (params) {

            var active_failures = params.active_failures,
                total_hosts = params.total_hosts,
                tip, failures, html_class;

            // Return values for use on host status indicator

            if (active_failures > 0) {
                tip = total_hosts + ((total_hosts === 1) ? ' host' : ' hosts') + '. ' + active_failures + ' with failed jobs.';
                html_class = 'true';
                failures = true;
            } else {
                failures = false;
                if (total_hosts === 0) {
                    // no hosts
                    tip = "Group contains 0 hosts.";
                    html_class = 'na';
                } else {
                    // many hosts with 0 failures
                    tip = total_hosts + ((total_hosts === 1) ? ' host' : ' hosts') + '. No job failures';
                    html_class = 'false';
                }
            }

            return {
                tooltip: tip,
                failures: failures,
                'class': html_class
            };
        };
    }
])

.factory('GetSyncStatusMsg', [
    function () {
        return function (params) {

            var status = params.status,
                launch_class = '',
                launch_tip = 'Start sync process',
                stat, stat_class, status_tip;
            
            stat = status;
            stat_class = 'icon-cloud-' + stat;

            switch (status) {
            case 'never updated':
                stat = 'never';
                stat_class = 'icon-cloud-na disabled';
                status_tip = 'Sync not performed. Click <i class="fa fa-exchange"></i> to start it now.';
                break;
            case 'none':
            case '':
                launch_class = 'btn-disabled';
                stat = 'n/a';
                stat_class = 'icon-cloud-na disabled';
                status_tip = 'Cloud source not configured. Click <i class="fa fa-pencil"></i> to update.';
                launch_tip = status_tip;
                break;
            case 'failed':
                status_tip = 'Sync failed. Click to view log.';
                break;
            case 'successful':
                status_tip = 'Sync completed. Click to view log.';
                break;
            case 'updating':
                status_tip = 'Sync running';
                break;
            }

            return {
                'class': stat_class,
                tooltip: status_tip,
                status: stat,
                'launch_class': launch_class,
                'launch_tip': launch_tip
            };
        };
    }
])

.factory('SourceChange', ['GetBasePath', 'CredentialList', 'LookUpInit', 'Empty', 'Wait', 'ParseTypeChange',
    function (GetBasePath, CredentialList, LookUpInit, Empty, Wait, ParseTypeChange) {
        return function (params) {

            var scope = params.scope,
                form = params.form,
                kind, url, callback;

            if (!Empty(scope.source)) {
                if (scope.source.value === 'file') {
                    scope.sourcePathRequired = true;
                } else {
                    scope.sourcePathRequired = false;
                    // reset fields
                    scope.source_path = '';
                    scope[form.name + '_form'].source_path.$setValidity('required', true);
                }
                if (scope.source.value === 'rax') {
                    scope.source_region_choices = scope.rax_regions;
                    //$('#s2id_group_source_regions').select2('data', []);
                    $('#s2id_source_source_regions').select2('data', [{
                        id: 'all',
                        text: 'All'
                    }]);
                } else if (scope.source.value === 'ec2') {
                    scope.source_region_choices = scope.ec2_regions;
                    //$('#s2id_group_source_regions').select2('data', []);
                    $('#s2id_source_source_regions').select2('data', [{
                        id: 'all',
                        text: 'All'
                    }]);
                }
                if (scope.source.value === 'rax' || scope.source.value === 'ec2') {
                    kind = (scope.source.value === 'rax') ? 'rax' : 'aws';
                    url = GetBasePath('credentials') + '?cloud=true&kind=' + kind;
                    LookUpInit({
                        url: url,
                        scope: scope,
                        form: form,
                        list: CredentialList,
                        field: 'credential'
                    });

                    if ($('#group_tabs .active a').text() === 'Source' && scope.source.value === 'ec2') {
                        callback = function(){ Wait('stop'); };
                        Wait('start');
                        ParseTypeChange({ scope: scope, variable: 'source_vars', parse_variable: form.fields.source_vars.parseTypeName,
                            field_id: 'source_source_vars', onReady: callback });
                    }
                }
            }
        };
    }
])


// Cancel a pending or running inventory sync
.factory('GroupsCancelUpdate', ['Rest', 'ProcessErrors', 'Alert', 'Wait', 'Find',
    function (Rest, ProcessErrors, Alert, Wait, Find) {
        return function (params) {

            var scope = params.scope,
                id = params.tree_id,
                group;

            if (scope.removeCancelUpdate) {
                scope.removeCancelUpdate();
            }
            scope.removeCancelUpdate = scope.$on('CancelUpdate', function (e, url) {
                // Cancel the update process
                Rest.setUrl(url);
                Rest.post()
                    .success(function () {
                        Wait('stop');
                        Alert('Inventory Sync Cancelled', 'Your request to cancel the sync process was submitted to the task manger. ' +
                            'Click the <i class="fa fa-refresh fa-lg"></i> button to monitor the status.', 'alert-info');
                    })
                    .error(function (data, status) {
                        Wait('stop');
                        ProcessErrors(scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. POST status: ' + status
                        });
                    });
            });

            if (scope.removeCheckCancel) {
                scope.removeCheckCancel();
            }
            scope.removeCheckCancel = scope.$on('CheckCancel', function (e, last_update, current_update) {
                // Check that we have access to cancelling an update
                var url = (current_update) ? current_update : last_update;
                url += 'cancel/';
                Rest.setUrl(url);
                Rest.get()
                    .success(function (data) {
                        if (data.can_cancel) {
                            scope.$emit('CancelUpdate', url);
                        } else {
                            Wait('stop');
                            Alert('Cancel Inventory Sync', 'Either you do not have access or the sync process completed.<br /> ' +
                                'Click the <i class="fa fa-refresh fa-lg"></i> button to view the latest status.', 'alert-info');
                        }
                    })
                    .error(function (data, status) {
                        Wait('stop');
                        ProcessErrors(scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. GET status: ' + status
                        });
                    });
            });

            // Cancel the update process
            group = Find({ list: scope.groups, key: 'id', val: id });
            scope.selected_tree_id = group.id;
            scope.selected_group_id = group.group_id;

            if (group && (group.status === 'updating' || group.status === 'pending')) {
                // We found the group, and there is a running update
                Wait('start');
                Rest.setUrl(group.related.inventory_source);
                Rest.get()
                    .success(function (data) {
                        scope.$emit('CheckCancel', data.related.last_update, data.related.current_update);
                    })
                    .error(function (data, status) {
                        Wait('stop');
                        ProcessErrors(scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + group.related.inventory_source + ' failed. GET status: ' + status
                        });
                    });
            } else {
                Alert('Cancel Inventory Sync', 'The sync process completed. Click the <i class="fa fa-refresh fa-lg"></i> to' +
                    ' view the latest status.', 'alert-info');
            }

        };
    }
])

.factory('GroupsAdd', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GroupForm', 'GenerateForm',
    'Prompt', 'ProcessErrors', 'GetBasePath', 'ParseTypeChange', 'Wait', 'GetChoices',
    'GetSourceTypeOptions', 'LookUpInit', 'BuildTree', 'SourceChange', 'WatchInventoryWindowResize', 'ToJSON',
    function ($rootScope, $location, $log, $routeParams, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, ParseTypeChange, Wait, GetChoices, GetSourceTypeOptions, LookUpInit, BuildTree,
        SourceChange, WatchInventoryWindowResize, ToJSON) {
        return function (params) {

            var inventory_id = params.inventory_id,
                group_id = (params.group_id !== undefined) ? params.group_id : null,
                parent_scope = params.scope,
                defaultUrl = (group_id !== null) ? GetBasePath('groups') + group_id + '/children/' :
                    GetBasePath('inventory') + inventory_id + '/groups/',
                form = GroupForm,
                generator = GenerateForm,
                scope = generator.inject(form, { mode: 'add', modal: true, related: false, show_modal: false }),
                choicesReady;

            scope.formModalActionLabel = 'Save';
            scope.formModalCancelShow = true;
            scope.source = null;
            generator.reset();
            
            scope[form.fields.source_vars.parseTypeName] = 'yaml';
            scope.parseType = 'yaml';
            ParseTypeChange({ scope: scope, field_id: 'group_variables' });

            $('#group_tabs a[data-toggle="tab"]').on('show.bs.tab', function (e) {
                var callback = function(){ Wait('stop'); };
                if ($(e.target).text() === 'Properties') {
                    Wait('start');
                    ParseTypeChange({ scope: scope, field_id: 'group_variables', onReady: callback });
                }
                else {
                    if (scope.source && scope.source.value === 'ec2') {
                        Wait('start');
                        ParseTypeChange({ scope: scope, variable: 'source_vars', parse_variable: form.fields.source_vars.parseTypeName,
                            field_id: 'group_source_vars', onReady: callback });
                    }
                }
            });

            if (scope.removeAddTreeRefreshed) {
                scope.removeAddTreeRefreshed();
            }
            scope.removeAddTreeRefreshed = scope.$on('GroupTreeRefreshed', function () {
                $rootScope.formModalHeader = null;
                $rootScope.formModalCancleShow = null;
                $rootScope.formModalActionLabel = null;
                Wait('stop');
                $('#form-modal').modal('hide');
                scope.removeAddTreeRefreshed();
            });

            if (scope.removeSaveComplete) {
                scope.removeSaveComplete();
            }
            scope.removeSaveComplete = scope.$on('SaveComplete', function (e, group_id, error) {
                if (!error) {
                    if (scope.searchCleanup) {
                        scope.searchCleanup();
                    }
                    scope.formModalActionDisabled = false;
                    BuildTree({
                        scope: parent_scope,
                        inventory_id: inventory_id,
                        refresh: true,
                        new_group_id: group_id
                    });
                    WatchInventoryWindowResize();
                }
            });

            if (scope.removeFormSaveSuccess) {
                scope.removeFormSaveSuccess();
            }
            scope.removeFormSaveSuccess = scope.$on('formSaveSuccess', function (e, group_id, url) {

                // Source data gets stored separately from the group. Validate and store Source
                // related fields, then call SaveComplete to wrap things up.

                var parseError = false,
                    data = {},
                    regions, r, i;

                // Update the selector tree with new group name, descr
                //SetNodeName({ scope: scope['selectedNode'], group_id: group_id,
                //    name: scope.name, description: scope.description });

                if (scope.source.value !== null && scope.source.value !== '') {
                    data.group = group_id;
                    data.source = scope.source.value;
                    data.source_path = scope.source_path;
                    data.credential = scope.credential;
                    data.overwrite = scope.overwrite;
                    data.overwrite_vars = scope.overwrite_vars;
                    data.update_on_launch = scope.update_on_launch;
                    
                    // Create a string out of selected list of regions
                    regions = $('#s2id_group_source_regions').select2("data");
                    r = [];
                    for (i = 0; i < regions.length; i++) {
                        r.push(regions[i].id);
                    }
                    data.source_regions = r.join();

                    if (scope.source.value === 'ec2') {
                        data.source_vars = ToJSON(scope.envParseType, scope.source_vars, true);
                    }

                    if (!parseError) {
                        Rest.setUrl(url);
                        Rest.put(data)
                            .success(function () {
                                scope.$emit('SaveComplete', group_id, false);
                            })
                            .error(function (data, status) {
                                scope.$emit('SaveComplete', group_id, true);
                                ProcessErrors(scope, data, status, form, {
                                    hdr: 'Error!',
                                    msg: 'Failed to update group inventory source. PUT status: ' + status
                                });
                            });
                    }
                } else {
                    // No source value
                    scope.$emit('SaveComplete', group_id, false);
                }
            });

            // Cancel
            scope.cancelModal = function () {
                if (scope.searchCleanup) {
                    scope.searchCleanup();
                }
                WatchInventoryWindowResize();
            };

            // Save
            scope.formModalAction = function () {
                var data;
                Wait('start');
                scope.formModalActionDisabled = true;
                data = {
                    name: scope.name,
                    description: scope.description
                };
                if (inventory_id) {
                    data.inventory = inventory_id;
                }
                data.variables = ToJSON(scope.parseType, scope.variables, true);
                Rest.setUrl(defaultUrl);
                Rest.post(data)
                    .success(function (data) {
                        scope.$emit('formSaveSuccess', data.id, GetBasePath('inventory_sources') + data.id + '/');
                    })
                    .error(function (data, status) {
                        Wait('stop');
                        scope.formModalActionDisabled = false;
                        ProcessErrors(scope, data, status, form, { hdr: 'Error!',
                            msg: 'Failed to add new group. POST returned status: ' + status });
                    });
            };

            scope.sourceChange = function () {
                SourceChange({ scope: scope, form: GroupForm });
            };

            choicesReady = 0;

            if (scope.removeChoicesReady) {
                scope.removeChoicesReady();
            }
            scope.removeChoicesReady = scope.$on('choicesReadyGroup', function () {
                choicesReady++;
                if (choicesReady === 2) {
                    $('#form-modal').modal('show');
                    Wait('stop');
                }
            });

            // Load options for source regions
            GetChoices({
                scope: scope,
                url: GetBasePath('inventory_sources'),
                field: 'source_regions',
                variable: 'rax_regions',
                choice_name: 'rax_region_choices',
                callback: 'choicesReadyGroup'
            });

            GetChoices({
                scope: scope,
                url: GetBasePath('inventory_sources'),
                field: 'source_regions',
                variable: 'ec2_regions',
                choice_name: 'ec2_region_choices',
                callback: 'choicesReadyGroup'
            });

            GetSourceTypeOptions({
                scope: scope,
                variable: 'source_type_options'
            });

            Wait('start');

        };
    }
])

/**
 * 
 * Add the list of schedules to the Group Edit modal
 *
 */
.factory('ScheduleList', ['ScheduleEdit', 'SchedulesList', 'GenerateList', 'SearchInit', 'PaginateInit', 'Rest', 'PageRangeSetup',
'Wait', 'ProcessErrors', 'Find',
function(ScheduleEdit, SchedulesList, GenerateList, SearchInit, PaginateInit, Rest, PageRangeSetup, Wait, ProcessErrors, Find) {
    return function(params) {
        var parent_scope = params.scope,
            scope, url, list;

        // Clean up
        $('#schedules-list').hide().empty();
        $('#schedules-form-container').hide();
        $('#schedules-form').empty();
        $('.tooltip').each(function () {
            $(this).remove();
        });
        $('.popover').each(function () {
            $(this).remove();
        });
        
        // Add schedules list
        list = angular.copy(SchedulesList);
        delete list.fields.dtend;
        delete list.actions.stream;
        list.well = false;
        scope = GenerateList.inject(list, {
            mode: 'edit',
            id: 'schedules-list',
            breadCrumbs: false,
            searchSize: 'col-lg-6 col-md-5 col-sm-5 col-xs-5'
        });

        $('#schedules-list').show();

        // Change later to use GetBasePath(base)
        url = '/static/sample/data/schedules/inventory/data.json';
        SearchInit({
            scope: scope,
            set: 'schedules',
            list: SchedulesList,
            url: url
        });
        PaginateInit({
            scope: scope,
            list: SchedulesList,
            url: url
        });
        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                var i, modifier;
                PageRangeSetup({
                    scope: scope,
                    count: data.count,
                    next: data.next,
                    previous: data.previous,
                    iterator: SchedulesList.iterator
                });
                scope[SchedulesList.iterator + 'Loading'] = false;
                for (i = 1; i <= 3; i++) {
                    modifier = (i === 1) ? '' : i;
                    scope[SchedulesList.iterator + 'HoldInput' + modifier] = false;
                }
                scope.schedules = data.results;
                window.scrollTo(0, 0);
                Wait('stop');
                scope.$emit('PostRefresh');
                scope.schedules = data.results;
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + ' failed. GET returned: ' + status });
            });

        scope.editSchedule = function(id) {
            var schedule = Find({ list: scope[SchedulesList.name], key: 'id', val: id });
            ScheduleEdit({ scope: parent_scope, schedule: schedule });
        };
    };
}])


/**
 *
 * Remove the schedule list, add the schedule widget and populate it with an rrule
 *
 */
.factory('ScheduleEdit', ['SchedulerInit', 'Rest', 'Wait',
function(SchedulerInit, Rest, Wait) {
    return function(params) {
        var parent_scope = params.scope,
            schedule = params.schedule,
            scope = parent_scope.$new(),
            scheduler,
            target,
            callback,
            list,
            restore,
            container;

        Wait('start');
        list = $('#schedules-list');
        target = $('#schedules-form');
        container = $('#schedules-form-container');

        // Clean up any lingering stuff
        container.hide();
        target.empty();
        $('.tooltip').each(function () {
                $(this).remove();
            });
        $('.popover').each(function () {
            $(this).remove();
        });

        // Insert the scheduler widget into the hidden div
        scheduler = SchedulerInit({ scope: scope, requireFutureStartTime: false });
        scheduler.inject('schedules-form', false);
        scheduler.clear();
        scope.showRRuleDetail = false;
        parent_scope.schedulesTitle = 'Edit Schedule';
        
        // display the scheduler widget
        callback = function() {
            Wait('stop');
            container.show('slide', { direction: 'left' }, 500);
            $('#group-save-button').prop('disabled', true);
            scope.$apply(function() {
                scheduler.setRRule(schedule.rrule);
                scheduler.setName(schedule.name);
            });
        };
        list.hide({ complete: callback, duration: 300 });

        restore = function() {
            $('#group-save-button').prop('disabled', false);
            list.show('slide', { direction: 'right' }, 500);
            //refresh the list
        };

        parent_scope.saveScheduleForm = function() {
            var newSchedule,
                url = '/static/sample/data/schedules/inventory/data.json';
            if (scheduler.isValid()) {
                scope.schedulerIsValid = true;
                Wait('start');
                newSchedule = scheduler.getValue();
                schedule.name = newSchedule.name;
                schedule.rrule = newSchedule.rrule;
                Rest.setUrl(url);
                Rest.post(schedule)
                    .success(function(){
                        Wait('stop');
                        container.hide('slide', { direction: 'right' }, 500, restore);
                    })
                    .error(function(){
                        Wait('stop');
                        container.hide('slide', { direction: 'right' }, 500, restore);
                    });
            }
            else {
                scope.schedulerIsValid = false;
            }
        };

        parent_scope.cancelScheduleForm = function() {
            container.hide('slide', { direction: 'right' }, 500, restore);
        };
    };
}])


.factory('GroupsEdit', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GroupForm', 'GenerateForm',
    'Prompt', 'ProcessErrors', 'GetBasePath', 'SetNodeName', 'ParseTypeChange', 'GetSourceTypeOptions', 'InventoryUpdate',
    'LookUpInit', 'Empty', 'Wait', 'GetChoices', 'UpdateGroup', 'SourceChange', 'Find','WatchInventoryWindowResize',
    'ParseVariableString', 'ToJSON', 'ScheduleList', 'SourceForm',
    function ($rootScope, $location, $log, $routeParams, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, SetNodeName, ParseTypeChange, GetSourceTypeOptions, InventoryUpdate, LookUpInit, Empty, Wait,
        GetChoices, UpdateGroup, SourceChange, Find, WatchInventoryWindowResize, ParseVariableString, ToJSON, ScheduleList,
        SourceForm) {
        return function (params) {

            var parent_scope = params.scope,
                group_id = params.group_id,
                tree_id = params.tree_id,
                inventory_id = params.inventory_id,
                groups_reload = params.groups_reload,
                generator = GenerateForm,
                defaultUrl = GetBasePath('groups') + group_id + '/',
                master = {},
                choicesReady,
                modal_scope = parent_scope.$new(),
                properties_scope = parent_scope.$new(),
                sources_scope = parent_scope.$new(),
                x, y, ww, wh, maxrows;
            
            generator.inject(GroupForm, { mode: 'edit', id: 'properties-tab', breadCrumbs: false, related: false, scope: properties_scope });
            generator.inject(SourceForm, { mode: 'edit', id: 'sources-tab', breadCrumbs: false, related: false, scope: sources_scope });
            
            //generator.reset();
            
            GetSourceTypeOptions({ scope: sources_scope, variable: 'source_type_options' });
            sources_scope.source = SourceForm.fields.source['default'];
            sources_scope.sourcePathRequired = false;
            sources_scope[SourceForm.fields.source_vars.parseTypeName] = 'yaml';
            properties_scope.parseType = 'yaml';

            function waitStop() { Wait('stop'); }
            
            // Attempt to create the largest textarea field that will fit on the window. Minimum 
            // height is 6 rows, so on short windows you will see vertical scrolling
            function textareaResize(textareaID) {
                var textArea, formHeight, model, windowHeight, offset, rows;
                textArea = $('#' + textareaID);
                if (properties_scope.codeMirror) {
                    model = textArea.attr('ng-model');
                    properties_scope[model] = properties_scope.codeMirror.getValue();
                    properties_scope.codeMirror.destroy();
                }
                textArea.attr('rows', 1);
                formHeight = $('#group_form').height();
                windowHeight = $('#group-modal-dialog').height() - 20;   //leave a margin of 20px
                offset = Math.floor(windowHeight - formHeight);
                rows = Math.floor(offset / 24);
                rows = (rows < 6) ? 6 : rows;
                textArea.attr('rows', rows);
                while(rows > 6 && $('#group_form').height() > $('#group-modal-dialog').height()) {
                    rows--;
                    textArea.attr('rows', rows);
                }
                ParseTypeChange({ scope: properties_scope, field_id: textareaID, onReady: waitStop });
            }

            // Set modal dimensions based on viewport width
            ww = $(document).width();
            wh = $('body').height();
            if (ww > 1199) {
                // desktop
                x = 675;
                y = (750 > wh) ? wh - 20 : 750;
                maxrows = 18;
            } else if (ww <= 1199 && ww >= 768) {
                x = 550;
                y = (620 > wh) ? wh - 15 : 620;
                maxrows = 12;
            } else {
                x = (ww - 20);
                y = (500 > wh) ? wh : 500;
                maxrows = 10;
            }

            // Create the modal
            $('#group-modal-dialog').dialog({
                buttons: {
                    'Cancel': function() {
                        modal_scope.cancelModal();
                    },
                    'Save': function () {
                        modal_scope.saveGroup();
                    }
                },
                modal: true,
                width: x,
                height: y,
                autoOpen: false,
                minWidth: 440,
                title: 'Edit Group',
                create: function () {
                    $('.ui-dialog[aria-describedby="group-modal-dialog"]').find('.ui-dialog-titlebar button').empty().attr({'class': 'close'}).text('x');
                    $('.ui-dialog[aria-describedby="group-modal-dialog"]').find('.ui-dialog-buttonset button').each(function () {
                        var c, h, i, l;
                        l = $(this).text();
                        if (l === 'Cancel') {
                            h = "fa-times";
                            c = "btn btn-default";
                            i = "group-close-button";
                            $(this).attr({
                                'class': c,
                                'id': i
                            }).html("<i class=\"fa " + h + "\"></i> Cancel");
                        } else if (l === 'Save') {
                            h = "fa-check";
                            c = "btn btn-primary";
                            i = "group-save-button";
                            $(this).attr({
                                'class': c,
                                'id': i
                            }).html("<i class=\"fa " + h + "\"></i> Save");
                        }
                    });
                },
                resizeStop: function () {
                    // for some reason, after resizing dialog the form and fields (the content) doesn't expand to 100%
                    var dialog = $('.ui-dialog[aria-describedby="group-modal-dialog"]'),
                        content = dialog.find('#group-modal-dialog');
                    content.width(dialog.width() - 28);
                    if ($('#group_tabs .active a').text() === 'Properties') {
                        textareaResize('group_variables', properties_scope);
                    }
                },
                close: function () {
                    // Destroy on close
                    $('.tooltip').each(function () {
                        // Remove any lingering tooltip <div> elements
                        $(this).remove();
                    });
                    $('.popover').each(function () {
                        // remove lingering popover <div> elements
                        $(this).remove();
                    });
                    $('#group-modal-dialog').dialog('destroy');
                    $('#group-modal-dialog').hide();
                    modal_scope.cancelModal();
                },
                open: function () {
                    $('#group_name').focus();
                    Wait('stop');
                }
            });

            $('#group_tabs a[data-toggle="tab"]').on('show.bs.tab', function (e) {
                if ($(e.target).text() === 'Properties') {
                    Wait('start');
                    setTimeout(function(){ textareaResize('group_variables'); }, 300);
                }
                else if ($(e.target).text() === 'Source') {
                    if (sources_scope.source && sources_scope.source.value === 'ec2') {
                        Wait('start');
                        ParseTypeChange({ scope: sources_scope, variable: 'source_vars', parse_variable: SourceForm.fields.source_vars.parseTypeName,
                            field_id: 'source_source_vars', onReady: waitStop });
                    }
                }
                else if ($(e.target).text() === 'Schedule') {
                    ScheduleList({ scope: parent_scope });
                }
            });

            if (modal_scope.groupVariablesLoadedRemove) {
                modal_scope.groupVariablesLoadedRemove();
            }
            modal_scope.groupVariablesLoadedRemove = modal_scope.$on('groupVariablesLoaded', function () {
                $('#group_tabs a:first').tab('show');
                Wait('start');
                $('#group-modal-dialog').dialog('open');
                setTimeout(function() { textareaResize('group_variables', properties_scope); }, 300);
            });

            // After the group record is loaded, retrieve related data
            if (modal_scope.groupLoadedRemove) {
                modal_scope.groupLoadedRemove();
            }
            modal_scope.groupLoadedRemove = modal_scope.$on('groupLoaded', function () {
                if (properties_scope.variable_url) {
                    // get group variables
                    Rest.setUrl(properties_scope.variable_url);
                    Rest.get()
                        .success(function (data) {
                            properties_scope.variables = ParseVariableString(data);
                            master.variables = properties_scope.variables;
                            modal_scope.$emit('groupVariablesLoaded');
                        })
                        .error(function (data, status) {
                            properties_scope.variables = null;
                            ProcessErrors(modal_scope, data, status, null, { hdr: 'Error!',
                                msg: 'Failed to retrieve group variables. GET returned status: ' + status });
                        });
                } else {
                    properties_scope.variables = "---";
                    master.variables = properties_scope.variables;
                    properties_scope.$emit('groupVariablesLoaded');
                }
                
                if (sources_scope.source_url) {
                    // get source data
                    Rest.setUrl(sources_scope.source_url);
                    Rest.get()
                        .success(function (data) {
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
                                    for (i = 0; i < sources_scope.source_type_options.length; i++) {
                                        if (sources_scope.source_type_options[i].value === data.source) {
                                            sources_scope.source = sources_scope.source_type_options[i];
                                            found = true;
                                        }
                                    }
                                    if (!found || sources_scope.source.value === "") {
                                        sources_scope.groupUpdateHide = true;
                                    } else {
                                        sources_scope.groupUpdateHide = false;
                                    }
                                    master.source = sources_scope.source;
                                } else if (fld === 'source_vars') {
                                    // Parse source_vars, converting to YAML.  
                                    sources_scope.source_vars = ParseVariableString(data.source_vars);
                                    master.source_vars = sources_scope.variables;
                                } else if (data[fld]) {
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

                            sources_scope.sourceChange(); //set defaults that rely on source value

                            if (data.source_regions) {
                                if (data.source === 'ec2' || data.source === 'rax') {
                                    set = (data.source === 'ec2') ? sources_scope.ec2_regions : sources_scope.rax_regions;
                                    opts = [];
                                    list = data.source_regions.split(',');
                                    for (i = 0; i < list.length; i++) {
                                        for (j = 0; j < set.length; j++) {
                                            if (list[i] === set[j].value) {
                                                opts.push({
                                                    id: set[j].value,
                                                    text: set[j].label
                                                });
                                            }
                                        }
                                    }
                                    master.source_regions = opts;
                                    $('#s2id_source_source_regions').select2('data', opts);
                                }
                            } else {
                                // If empty, default to all
                                master.source_regions = [{
                                    id: 'all',
                                    text: 'All'
                                }];
                                $('#s2id_source_source_regions').select2('data', master.source_regions);
                            }
                            sources_scope.group_update_url = data.related.update;
                            //Wait('stop');
                        })
                        .error(function (data, status) {
                            sources_scope.source = "";
                            ProcessErrors(modal_scope, data, status, null, { hdr: 'Error!',
                                msg: 'Failed to retrieve inventory source. GET status: ' + status });
                        });
                }
            });

            if (modal_scope.removeChoicesComplete) {
                modal_scope.removeChoicesComplete();
            }
            modal_scope.removeChoicesComplete = modal_scope.$on('choicesCompleteGroup', function () {
                // Retrieve detail record and prepopulate the form
                Rest.setUrl(defaultUrl);
                Rest.get()
                    .success(function (data) {
                        for (var fld in GroupForm.fields) {
                            if (data[fld]) {
                                properties_scope[fld] = data[fld];
                                master[fld] = properties_scope[fld];
                            }
                        }
                        properties_scope.variable_url = data.related.variable_data;
                        sources_scope.source_url = data.related.inventory_source;
                        modal_scope.$emit('groupLoaded');
                    })
                    .error(function (data, status) {
                        ProcessErrors(modal_scope, data, status, { hdr: 'Error!',
                            msg: 'Failed to retrieve group: ' + defaultUrl + '. GET status: ' + status });
                    });
            });

            choicesReady = 0;

            if (sources_scope.removeChoicesReady) {
                sources_scope.removeChoicesReady();
            }
            sources_scope.removeChoicesReady = sources_scope.$on('choicesReadyGroup', function () {
                choicesReady++;
                if (choicesReady === 2) {
                    modal_scope.$emit('choicesCompleteGroup');
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

            Wait('start');

            if (modal_scope.removeSaveComplete) {
                modal_scope.removeSaveComplete();
            }
            modal_scope.removeSaveComplete = modal_scope.$on('SaveComplete', function (e, error) {
                if (!error) {
                    // Update the view with any changes
                    if (groups_reload) {
                        UpdateGroup({
                            scope: parent_scope,
                            group_id: group_id,
                            properties: {
                                name: properties_scope.name,
                                description: properties_scope.description,
                                has_inventory_sources: (sources_scope.source && sources_scope.source.value) ? true : false,
                                source: (sources_scope.source && sources_scope.source.value) ? sources_scope.source.value : ''
                            }
                        });
                    } else if (parent_scope.home_groups) {
                        // When home.groups controller is calling, update the groups array
                        var g = Find({
                            list: parent_scope.home_groups,
                            key: 'id',
                            val: group_id
                        });
                        if (g) {
                            g.name = properties_scope.name;
                            g.description = properties_scope.description;
                        }
                    }

                    //Clean up
                    if (modal_scope.searchCleanUp) {
                        modal_scope.searchCleanup();
                    }

                    $('#group-modal-dialog').dialog('close');

                    // Change the selected group
                    if (groups_reload && parent_scope.selected_tree_id !== tree_id) {
                        parent_scope.showHosts(tree_id, group_id, false);
                    } else {
                        Wait('stop');
                    }
                    WatchInventoryWindowResize();
                }
            });

            if (modal_scope.removeFormSaveSuccess) {
                modal_scope.removeFormSaveSuccess();
            }
            modal_scope.removeFormSaveSuccess = modal_scope.$on('formSaveSuccess', function () {

                // Source data gets stored separately from the group. Validate and store Source
                // related fields, then call SaveComplete to wrap things up.

                var parseError = false,
                    regions, r, i,
                    data = {
                        group: group_id,
                        source: ((sources_scope.source && sources_scope.source.value) ? sources_scope.source.value : ''),
                        source_path: sources_scope.source_path,
                        credential: sources_scope.credential,
                        overwrite: sources_scope.overwrite,
                        overwrite_vars: sources_scope.overwrite_vars,
                        update_on_launch: sources_scope.update_on_launch
                    };

                // Create a string out of selected list of regions
                regions = $('#s2id_source_source_regions').select2("data");
                r = [];
                for (i = 0; i < regions.length; i++) {
                    r.push(regions[i].id);
                }
                data.source_regions = r.join();

                if (sources_scope.source && sources_scope.source.value === 'ec2') {
                    // for ec2, validate variable data
                    data.source_vars = ToJSON(sources_scope.envParseType, sources_scope.source_vars, true);
                }

                if (!parseError) {
                    Rest.setUrl(sources_scope.source_url);
                    Rest.put(data)
                        .success(function () {
                            modal_scope.$emit('SaveComplete', false);
                        })
                        .error(function (data, status) {
                            modal_scope.$emit('SaveComplete', true);
                            ProcessErrors(sources_scope, data, status, SourceForm, { hdr: 'Error!',
                                msg: 'Failed to update group inventory source. PUT status: ' + status });
                        });
                }
            });
            
            // Cancel
            modal_scope.cancelModal = function () {
                try {
                    $('#group-modal-dialog').dialog('close');
                }
                catch(e) {
                    //ignore
                }
                if (modal_scope.searchCleanup) {
                    modal_scope.searchCleanup();
                }
                WatchInventoryWindowResize();
            };

            // Save
            modal_scope.saveGroup = function () {
                Wait('start');
                var fld, data, json_data;

                json_data = ToJSON(properties_scope.parseType, properties_scope.variables);

                data = {};
                for (fld in GroupForm.fields) {
                    if (fld !== 'variables') {
                        data[fld] = properties_scope[fld];
                    }
                }

                data.inventory = inventory_id;

                Rest.setUrl(defaultUrl);
                Rest.put(data)
                    .success(function () {
                        if (properties_scope.variables) {
                            //update group variables
                            Rest.setUrl(properties_scope.variable_url);
                            Rest.put(json_data)
                                .success(function () {
                                    modal_scope.$emit('formSaveSuccess');
                                })
                                .error(function (data, status) {
                                    ProcessErrors(modal_scope, data, status, null, { hdr: 'Error!',
                                        msg: 'Failed to update group variables. PUT status: ' + status });
                                });
                        } else {
                            modal_scope.$emit('formSaveSuccess');
                        }
                    })
                    .error(function (data, status) {
                        Wait('stop');
                        ProcessErrors(properties_scope, data, status, GroupForm, { hdr: 'Error!',
                            msg: 'Failed to update group: ' + group_id + '. PUT status: ' + status
                        });
                    });
            };

            // Start the update process
            modal_scope.updateGroup = function () {
                if (sources_scope.source === "" || sources_scope.source === null) {
                    Alert('Missing Configuration', 'The selected group is not configured for updates. You must first edit the group, provide Source settings, ' +
                        'and then run an update.', 'alert-info');
                } else if (sources_scope.status === 'updating') {
                    Alert('Update in Progress', 'The inventory update process is currently running for group <em>' +
                        sources_scope.summary_fields.group.name + '</em>. Use the Refresh button to monitor the status.', 'alert-info');
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
            sources_scope.sourceChange = function () {
                SourceChange({ scope: sources_scope, form: SourceForm });
            };

        };
    }
])


.factory('GroupsDelete', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GroupForm', 'GenerateForm',
    'Prompt', 'ProcessErrors', 'GetBasePath', 'Wait', 'BuildTree', 'Find',
    function ($rootScope, $location, $log, $routeParams, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, Wait, BuildTree, Find) {
        return function (params) {
            // Delete the selected group node. Disassociates it from its parent.

            var scope = params.scope,
                tree_id = params.tree_id,
                inventory_id = params.inventory_id,
                node = Find({ list: scope.groups, key: 'id', val: tree_id }),
                url = GetBasePath('inventory') + inventory_id + '/groups/',
                action_to_take;

            action_to_take = function () {
                $('#prompt-modal').on('hidden.bs.modal', function () {
                    Wait('start');
                });
                $('#prompt-modal').modal('hide');
                Rest.setUrl(url);
                Rest.post({ id: node.group_id, disassociate: 1 })
                    .success(function () {
                        $('#prompt-modal').modal('hide');
                        scope.$emit('GroupDeleteCompleted'); // Signal a group refresh to start
                    })
                    .error(function (data, status) {
                        Wait('stop');
                        ProcessErrors(scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. POST returned status: ' + status
                        });
                    });
            };

            Prompt({
                hdr: 'Delete Group',
                body: '<p>Are you sure you want to delete group <em>' + node.name + '?</p>',
                action: action_to_take,
                'class': 'btn-danger'
            });
        };
    }
])


.factory('ShowUpdateStatus', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GenerateForm',
    'Prompt', 'ProcessErrors', 'GetBasePath', 'FormatDate', 'InventoryStatusForm', 'Wait', 'Empty', 'WatchInventoryWindowResize',
    function ($rootScope, $location, $log, $routeParams, Rest, Alert, GenerateForm, Prompt, ProcessErrors, GetBasePath,
        FormatDate, InventoryStatusForm, Wait, Empty, WatchInventoryWindowResize) {
        return function (params) {

            var group_name = params.group_name,
                last_update = params.last_update,
                generator = GenerateForm,
                form = InventoryStatusForm,
                license_error = params.license_error,
                maxrows, html, scope, ww, wh, x, y;

            function calcRows(content) {
                var n, rows;
                n = content.match(/\n/g);
                rows = (n) ? n.length : 1;
                return (rows > maxrows) ? maxrows : rows;
            }

            if (last_update === undefined || last_update === null || last_update === '') {
                Wait('stop');
                Alert('Missing Configuration', 'The selected group is not configured for inventory sync. ' +
                    'Edit the group and provide Source information.', 'alert-info');
            } else {
                html = "<div id=\"status-modal-dialog\" title=\"" + group_name + "- Inventory Sync\">\n" +
                    "<div id=\"form-container\" style=\"width: 100%;\"></div></div>\n";

                $('#inventory-modal-container').empty().append(html);
                scope = generator.inject(form, {
                    mode: 'edit',
                    id: 'form-container',
                    breadCrumbs: false,
                    related: false
                });

                // Set modal dimensions based on viewport width
                ww = $(document).width();
                wh = $('body').height();
                if (ww > 1199) {
                    // desktop
                    x = 675;
                    y = (750 > wh) ? wh - 20 : 750;
                    maxrows = 18;
                } else if (ww <= 1199 && ww >= 768) {
                    x = 550;
                    y = (620 > wh) ? wh - 15 : 620;
                    maxrows = 12;
                } else {
                    x = (ww - 20);
                    y = (500 > wh) ? wh : 500;
                    maxrows = 10;
                }

                // Create the modal
                $('#status-modal-dialog').dialog({
                    buttons: {
                        "OK": function () {
                            $(this).dialog("close");
                        }
                    },
                    modal: true,
                    width: x,
                    height: y,
                    autoOpen: false,
                    create: function () {
                        // fix the close button
                        $('.ui-dialog[aria-describedby="status-modal-dialog"]').find('.ui-dialog-titlebar button')
                            .empty().attr({
                                'class': 'close'
                            }).text('x');
                        // fix the OK button
                        $('.ui-dialog[aria-describedby="status-modal-dialog"]').find('.ui-dialog-buttonset button:first')
                            .attr({
                                'class': 'btn btn-primary'
                            });
                    },
                    resizeStop: function () {
                        // for some reason, after resizing dialog the form and fields (the content) doesn't expand to 100%
                        var dialog = $('.ui-dialog[aria-describedby="status-modal-dialog"]'),
                            content = dialog.find('#status-modal-dialog');
                        content.width(dialog.width() - 28);
                    },
                    close: function () {
                        // Destroy on close
                        $('.tooltip').each(function () {
                            // Remove any lingering tooltip <div> elements
                            $(this).remove();
                        });
                        $('.popover').each(function () {
                            // remove lingering popover <div> elements
                            $(this).remove();
                        });
                        $('#status-modal-dialog').dialog('destroy');
                        $('#inventory-modal-container').empty();
                        WatchInventoryWindowResize();
                    },
                    open: function () {
                        Wait('stop');
                    }
                });

                Rest.setUrl(last_update);
                Rest.get()
                    .success(function (data) {
                        for (var fld in form.fields) {
                            if (data[fld]) {
                                if (fld === 'created') {
                                    scope[fld] = FormatDate(new Date(data[fld]));
                                } else {
                                    scope[fld] = data[fld];
                                }
                            }
                        }
                        scope.license_error = license_error;
                        scope.status_rows = calcRows(data.status);
                        scope.stdout_rows = calcRows(data.result_stdout);
                        scope.traceback_rows = calcRows(data.result_traceback);
                        $('#status-modal-dialog').dialog('open');
                    })
                    .error(function (data, status) {
                        $('#form-modal').modal("hide");
                        ProcessErrors(scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to retrieve last update: ' + last_update + '. GET status: ' + status
                        });
                    });
            }

        };
    }
]);