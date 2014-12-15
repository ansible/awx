/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  GroupsHelper
 *
 *  Routines that handle group add/edit/delete on the Inventory tree widget.
 *
 */
   /**
 * @ngdoc function
 * @name helpers.function:Groups
 * @description    inventory tree widget add/edit/delete
*/
'use strict';

angular.module('GroupsHelper', [ 'RestServices', 'Utilities', 'ListGenerator', 'GroupListDefinition', 'SearchHelper',
    'PaginationHelpers', 'ListGenerator', 'AuthService', 'GroupsHelper', 'InventoryHelper', 'SelectionHelper',
    'JobSubmissionHelper', 'RefreshHelper', 'PromptDialog', 'CredentialsListDefinition', 'InventoryTree',
    'InventoryStatusDefinition', 'VariablesHelper', 'SchedulesListDefinition', 'SourceFormDefinition', 'LogViewerHelper',
    'SchedulesHelper' ])

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
                        scope.$emit('sourceTypeOptionsReady');
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to retrieve options for inventory_sources.source. OPTIONS status: ' + status
                        });
                    });
            }
        };
    }
])


.factory('ViewUpdateStatus', ['Rest', 'ProcessErrors', 'GetBasePath', 'Alert', 'Wait', 'Empty', 'Find', 'LogViewer',
    function (Rest, ProcessErrors, GetBasePath, Alert, Wait, Empty, Find, LogViewer) {
        return function (params) {

            var scope = params.scope,
                group_id = params.group_id,
                group = Find({ list: scope.groups, key: 'id', val: group_id });

            if (scope.removeSourceReady) {
                scope.removeSourceReady();
            }
            scope.removeSourceReady = scope.$on('SourceReady', function(e, url) {
                LogViewer({
                    scope: scope,
                    url: url
                });
            });

            if (group) {
                if (Empty(group.source)) {
                    // do nothing
                } else if (Empty(group.status) || group.status === "never updated") {
                    Alert('No Status Available', 'An inventory sync has not been performed for the selected group. Start the process by ' +
                        'clicking the <i class="fa fa-exchange"></i> button.', 'alert-info');
                } else {
                    Wait('start');
                    Rest.setUrl(group.related.inventory_source);
                    Rest.get()
                        .success(function (data) {
                            var url = (data.related.current_update) ? data.related.current_update : data.related.last_update;
                            scope.$emit('SourceReady', url);
                        })
                        .error(function (data, status) {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Failed to retrieve inventory source: ' + group.related.inventory_source +
                                    ' POST returned status: ' + status });
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
                html_class = 'error';
                failures = true;
            } else {
                failures = false;
                if (total_hosts === 0) {
                    // no hosts
                    tip = "Contains 0 hosts.";
                    html_class = 'none';
                } else {
                    // many hosts with 0 failures
                    tip = total_hosts + ((total_hosts === 1) ? ' host' : ' hosts') + '. No job failures';
                    html_class = 'success';
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

.factory('GetSyncStatusMsg', [ 'Empty',
    function (Empty) {
        return function (params) {

            var status = params.status,
                source = params.source,
                has_inventory_sources = params.has_inventory_sources,
                launch_class = '',
                launch_tip = 'Start sync process',
                stat, stat_class, status_tip;

            stat = status;
            stat_class = stat;

            switch (status) {
                case 'never updated':
                    stat = 'never';
                    stat_class = 'na';
                    status_tip = 'Sync not performed. Click <i class="fa fa-exchange"></i> to start it now.';
                    break;
                case 'none':
                case 'ok':
                case '':
                    launch_class = 'btn-disabled';
                    stat = 'n/a';
                    stat_class = 'na';
                    status_tip = 'Cloud source not configured. Click <i class="fa fa-pencil"></i> to update.';
                    launch_tip = 'Cloud source not configured.';
                    break;
                case 'canceled':
                    status_tip = 'Sync canceled. Click to view log.';
                    break;
                case 'failed':
                    status_tip = 'Sync failed. Click to view log.';
                    break;
                case 'successful':
                    status_tip = 'Sync completed. Click to view log.';
                    break;
                case 'pending':
                    status_tip = 'Sync pending.';
                    launch_class = "btn-disabled";
                    launch_tip = "Sync pending";
                    break;
                case 'updating':
                case 'running':
                    launch_class = "btn-disabled";
                    launch_tip = "Sync running";
                    status_tip = "Sync running. Click to view log.";
                    break;
            }

            if (has_inventory_sources && Empty(source)) {
                // parent has a source, therefore this group should not have a source
                launch_class = "btn-disabled";
                status_tip = 'Managed by an external cloud source.';
                launch_tip = 'Can only be updated by running a sync on the parent group.';
            }

            if (has_inventory_sources === false && Empty(source)) {
                launch_class = 'btn-disabled';
                status_tip = 'Cloud source not configured. Click <i class="fa fa-pencil"></i> to update.';
                launch_tip = 'Cloud source not configured.';
            }

            return {
                "class": stat_class,
                "tooltip": status_tip,
                "status": stat,
                "launch_class": launch_class,
                "launch_tip": launch_tip
            };
        };
    }
])

.factory('SourceChange', ['GetBasePath', 'CredentialList', 'LookUpInit', 'Empty', 'Wait', 'ParseTypeChange', 'CustomInventoryList' ,
    function (GetBasePath, CredentialList, LookUpInit, Empty, Wait, ParseTypeChange, CustomInventoryList) {
        return function (params) {

            var scope = params.scope,
                form = params.form,
                kind, url, callback, invUrl;

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
                    $('#source_form').removeClass('squeeze');
                } else if (scope.source.value === 'ec2') {
                    scope.source_region_choices = scope.ec2_regions;
                    $('#s2id_source_source_regions').select2('data', [{
                        id: 'all',
                        text: 'All'
                    }]);
                    scope.group_by_choices = scope.ec2_group_by;
                    $('#s2id_group_by').select2('data', []);
                    $('#source_form').addClass('squeeze');
                } else if (scope.source.value === 'gce') {
                    scope.source_region_choices = scope.gce_regions;
                    //$('#s2id_group_source_regions').select2('data', []);
                    $('#s2id_source_source_regions').select2('data', [{
                        id: 'all',
                        text: 'All'
                    }]);
                    $('#source_form').addClass('squeeze');
                } else if (scope.source.value === 'azure') {
                    scope.source_region_choices = scope.azure_regions;
                    //$('#s2id_group_source_regions').select2('data', []);
                    $('#s2id_source_source_regions').select2('data', [{
                        id: 'all',
                        text: 'All'
                    }]);
                    $('#source_form').addClass('squeeze');
                }
                if(scope.source.value==="custom"){
                    // need to filter the possible custom scripts by the organization defined for the current inventory
                    invUrl = GetBasePath('inventory_scripts') + '?organization='+scope.$parent.inventory.organization;
                    LookUpInit({
                        url: invUrl,
                        scope: scope,
                        form: form,
                        hdr: "Select Custom Inventory",
                        list: CustomInventoryList,
                        field: 'source_script',
                        input_type: 'radio'
                    });
                    scope.extra_vars = (Empty(scope.source_vars)) ? "---" : scope.source_vars;
                    ParseTypeChange({ scope: scope, variable: 'extra_vars', parse_variable: form.fields.extra_vars.parseTypeName,
                        field_id: 'source_extra_vars', onReady: callback });
                }
                if(scope.source.value==="vmware"){
                    scope.inventory_variables = (Empty(scope.source_vars)) ? "---" : scope.source_vars;
                    ParseTypeChange({ scope: scope, variable: 'inventory_variables', parse_variable: form.fields.inventory_variables.parseTypeName,
                        field_id: 'source_inventory_variables', onReady: callback });
                }
                if (scope.source.value === 'rax' || scope.source.value === 'ec2'|| scope.source.value==='gce' || scope.source.value === 'azure' || scope.source.value === 'vmware') {
                    kind = (scope.source.value === 'rax') ? 'rax' : (scope.source.value==='gce') ? 'gce' : (scope.source.value==='azure') ? 'azure' : (scope.source.value === 'vmware') ? 'vmware' : 'aws' ;
                    url = GetBasePath('credentials') + '?cloud=true&kind=' + kind;
                    LookUpInit({
                        url: url,
                        scope: scope,
                        form: form,
                        list: CredentialList,
                        field: 'credential',
                        input_type: "radio"
                    });
                    if ($('#group_tabs .active a').text() === 'Source' && (scope.source.value === 'ec2' )) {
                        callback = function(){ Wait('stop'); };
                        Wait('start');
                        scope.source_vars = (Empty(scope.source_vars)) ? "---" : scope.source_vars;
                        ParseTypeChange({ scope: scope, variable: 'source_vars', parse_variable: form.fields.source_vars.parseTypeName,
                            field_id: 'source_source_vars', onReady: callback });
                    }
                }
            }
        };
    }
])


// Cancel a pending or running inventory sync
.factory('GroupsCancelUpdate', ['Empty', 'Rest', 'ProcessErrors', 'Alert', 'Wait', 'Find',
    function (Empty, Rest, ProcessErrors, Alert, Wait, Find) {
        return function (params) {

            var scope = params.scope,
                id = params.id,
                group = params.group;

            if (scope.removeCancelUpdate) {
                scope.removeCancelUpdate();
            }
            scope.removeCancelUpdate = scope.$on('CancelUpdate', function (e, url) {
                // Cancel the update process
                Rest.setUrl(url);
                Rest.post()
                    .success(function () {
                        Wait('stop');
                        //Alert('Inventory Sync Cancelled', 'Request to cancel the sync process was submitted to the task manger. ' +
                        //    'Click the <i class="fa fa-refresh fa-lg"></i> button to monitor the status.', 'alert-info');
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
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
                        //} else {
                        //    Wait('stop');
                        //    Alert('Cancel Inventory Sync', 'The sync process completed. Click the <i class="fa fa-refresh fa-lg"></i> button to view ' +
                        //        'the latest status.', 'alert-info');
                        }
                        else {
                            Wait('stop');
                        }
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. GET status: ' + status
                        });
                    });
            });

            // Cancel the update process
            if (Empty(group)) {
                group = Find({ list: scope.groups, key: 'id', val: id });
                scope.selected_group_id = group.id;
            }

            if (group && (group.status === 'running' || group.status === 'pending')) {
                // We found the group, and there is a running update
                Wait('start');
                Rest.setUrl(group.related.inventory_source);
                Rest.get()
                    .success(function (data) {
                        scope.$emit('CheckCancel', data.related.last_update, data.related.current_update);
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + group.related.inventory_source + ' failed. GET status: ' + status
                        });
                    });
            }
        };
    }
])

/**
 *
 * Add the list of schedules to the Group Edit modal
 *
 */
.factory('GroupsScheduleListInit', ['GroupsScheduleEdit', 'SchedulesList', 'GenerateList', 'SearchInit', 'PaginateInit', 'Rest', 'PageRangeSetup',
'Wait', 'ProcessErrors', 'Find', 'ToggleSchedule', 'DeleteSchedule', 'GetBasePath', 'SchedulesListInit',
function(GroupsScheduleEdit, SchedulesList, GenerateList, SearchInit, PaginateInit, Rest, PageRangeSetup, Wait, ProcessErrors, Find,
ToggleSchedule, DeleteSchedule, GetBasePath, SchedulesListInit) {
    return function(params) {
        var schedule_scope = params.scope,
            url = params.url,
            list;

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
        GenerateList.inject(list, {
            mode: 'edit',
            id: 'schedules-list',
            breadCrumbs: false,
            searchSize: 'col-lg-6 col-md-5 col-sm-5 col-xs-5',
            scope: schedule_scope
        });

        $('#schedules-list').show();

        // Removing screws up /home/groups page
        // if (schedule_scope.removePostRefresh) {
        //    schedule_scope.removePostRefresh();
        //}
        schedule_scope.removePostRefresh = schedule_scope.$on('PostRefresh', function() {
            SchedulesListInit({
                scope: schedule_scope,
                list: list,
                choices: null
            });
        });
        SearchInit({
            scope: schedule_scope,
            set: 'schedules',
            list: SchedulesList,
            url: url
        });
        PaginateInit({
            scope: schedule_scope,
            list: SchedulesList,
            url: url,
            pageSize: 5
        });
        schedule_scope.search(list.iterator);

        schedule_scope.refreshSchedules = function() {
            schedule_scope.search(list.iterator);
        };

        schedule_scope.editSchedule = function(id) {
            GroupsScheduleEdit({ scope: schedule_scope, mode: 'edit', url: GetBasePath('schedules') + id + '/' });
        };

        schedule_scope.addSchedule = function() {
            GroupsScheduleEdit({ scope: schedule_scope, mode: 'add', url: url });
        };

        if (schedule_scope.removeSchedulesRefresh) {
            schedule_scope.removeSchedulesRefresh();
        }
        schedule_scope.removeSchedulesRefresh = schedule_scope.$on('SchedulesRefresh', function() {
            schedule_scope.search(list.iterator);
        });

        schedule_scope.toggleSchedule = function(event, id) {
            try {
                $(event.target).tooltip('hide');
            }
            catch(e) {
                // ignore
            }
            ToggleSchedule({
                scope: schedule_scope,
                id: id,
                callback: 'SchedulesRefresh'
            });
        };

        schedule_scope.deleteSchedule = function(id) {
            DeleteSchedule({
                scope: schedule_scope,
                id: id,
                callback: 'SchedulesRefresh'
            });
        };

    };
}])


.factory('SetSchedulesInnerDialogSize', [ function() {
    return function() {
        var height = $('#group-modal-dialog').outerHeight() - $('#group_tabs').outerHeight() - 25;
        height = height - 110 - $('#schedules-buttons').outerHeight();
        $('#schedules-form-container-body').height(height);
    };
}])


/**
 *
 * Remove the schedule list, add the schedule widget and populate it with an rrule
 *
 */
.factory('GroupsScheduleEdit', ['$compile','SchedulerInit', 'Rest', 'Wait', 'SetSchedulesInnerDialogSize', 'SchedulePost', 'ProcessErrors',
function($compile, SchedulerInit, Rest, Wait, SetSchedulesInnerDialogSize, SchedulePost, ProcessErrors) {
    return function(params) {
        var parent_scope = params.scope,
            mode = params.mode,  // 'add' or 'edit'
            url = params.url,
            scope = parent_scope.$new(),
            schedule = {},
            scheduler,
            target,
            showForm,
            list,
            detail,
            restoreList,
            container,
            elem;

        Wait('start');
        detail = $('#schedules-detail').hide();
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

        elem = angular.element(document.getElementById('schedules-form-container'));
        $compile(elem)(scope);

        if (scope.removeScheduleReady) {
            scope.removeScheduleReady();
        }
        scope.removeScheduleReady = scope.$on('ScheduleReady', function() {
            // Insert the scheduler widget into the hidden div
            scheduler = SchedulerInit({ scope: scope, requireFutureStartTime: false });
            scheduler.inject('schedules-form', false);
            scheduler.injectDetail('schedules-detail', false);
            scheduler.clear();
            scope.formShowing = true;
            scope.showRRuleDetail = false;
            scope.schedulesTitle = (mode === 'edit') ? 'Edit Schedule' : 'Create Schedule';

            // display the scheduler widget
            showForm = function() {
                Wait('stop');
                $('#schedules-overlay').width($('#schedules-tab')
                    .width()).height($('#schedules-tab').height()).show();
                container.width($('#schedules-tab').width() - 18);
                SetSchedulesInnerDialogSize();
                container.show('slide', { direction: 'left' }, 300);
                $('#group-save-button').prop('disabled', true);
                target.show();
                if (mode === 'edit') {
                    scope.$apply(function() {
                        scheduler.setRRule(schedule.rrule);
                        scheduler.setName(schedule.name);
                    });
                }
            };
            setTimeout(function() { showForm(); }, 1000);
        });

        restoreList = function() {
            $('#group-save-button').prop('disabled', false);
            list.show('slide', { direction: 'right' }, 500);
            $('#schedules-overlay').width($('#schedules-tab').width()).height($('#schedules-tab').height()).hide();
            parent_scope.refreshSchedules();
        };

        scope.showScheduleDetail = function() {
            if (scope.formShowing) {
                if (scheduler.isValid()) {
                    detail.width($('#schedules-form').width()).height($('#schedules-form').height());
                    target.hide();
                    detail.show();
                    scope.formShowing = false;
                }
            }
            else {
                detail.hide();
                target.show();
                scope.formShowing = true;
            }
        };

        if (scope.removeScheduleSaved) {
            scope.removeScheduleSaved();
        }
        scope.removeScheduleSaved = scope.$on('ScheduleSaved', function() {
            Wait('stop');
            container.hide('slide', { direction: 'right' }, 500, restoreList);
            scope.$destroy();
        });

        scope.saveScheduleForm = function() {
            if (scheduler.isValid()) {
                scope.schedulerIsValid = true;
                SchedulePost({
                    scope: scope,
                    url: url,
                    scheduler: scheduler,
                    callback: 'ScheduleSaved',
                    mode: mode,
                    schedule: schedule
                });
            }
            else {
                scope.schedulerIsValid = false;
            }
        };

        scope.cancelScheduleForm = function() {
            container.hide('slide', { direction: 'right' }, 500, restoreList);
            scope.$destroy();
        };

        if (mode === 'edit') {
            // Get the existing record
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    schedule = data;
                    if (!/DTSTART/.test(schedule.rrule)) {
                        schedule.rrule += ";DTSTART=" + schedule.dtstart.replace(/\.\d+Z$/,'Z');
                    }
                    schedule.rrule = schedule.rrule.replace(/ RRULE:/,';');
                    schedule.rrule = schedule.rrule.replace(/DTSTART:/,'DTSTART=');
                    scope.$emit('ScheduleReady');
                })
                .error(function(data,status){
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to get: ' + url + ' GET returned: ' + status });
                });
        }
        else {
            scope.$emit('ScheduleReady');
        }
    };
}])


.factory('GroupsEdit', ['$rootScope', '$location', '$log', '$routeParams', '$compile', 'Rest', 'Alert', 'GroupForm', 'GenerateForm',
    'Prompt', 'ProcessErrors', 'GetBasePath', 'SetNodeName', 'ParseTypeChange', 'GetSourceTypeOptions', 'InventoryUpdate',
    'LookUpInit', 'Empty', 'Wait', 'GetChoices', 'UpdateGroup', 'SourceChange', 'Find', 'WatchInventoryWindowResize',
    'ParseVariableString', 'ToJSON', 'GroupsScheduleListInit', 'SourceForm', 'SetSchedulesInnerDialogSize',
    function ($rootScope, $location, $log, $routeParams, $compile, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, SetNodeName, ParseTypeChange, GetSourceTypeOptions, InventoryUpdate, LookUpInit, Empty, Wait,
        GetChoices, UpdateGroup, SourceChange, Find, WatchInventoryWindowResize, ParseVariableString, ToJSON, GroupsScheduleListInit,
        SourceForm, SetSchedulesInnerDialogSize) {
        return function (params) {

            var parent_scope = params.scope,
                group_id = params.group_id,
                mode = params.mode,  // 'add' or 'edit'
                inventory_id = params.inventory_id,
                generator = GenerateForm,
                group_created = false,
                defaultUrl,
                master = {},
                choicesReady,
                modal_scope = parent_scope.$new(),
                properties_scope = parent_scope.$new(),
                sources_scope = parent_scope.$new(),
                elem, x, y, ww, wh, maxrows,
                group,
                schedules_url = '';

            if (mode === 'edit') {
                defaultUrl = GetBasePath('groups') + group_id + '/';
            }
            else {
                defaultUrl = (group_id !== null) ? GetBasePath('groups') + group_id + '/children/' :
                    GetBasePath('inventory') + inventory_id + '/groups/';
            }

            $('#properties-tab').empty();
            $('#sources-tab').empty();
            $('#schedules-list').empty();
            $('#schedules-form').empty();
            $('#schedules-detail').empty();

            elem = document.getElementById('group-modal-dialog');
            $compile(elem)(modal_scope);

            generator.inject(GroupForm, { mode: 'edit', id: 'properties-tab', breadCrumbs: false, related: false, scope: properties_scope });
            generator.inject(SourceForm, { mode: 'edit', id: 'sources-tab', breadCrumbs: false, related: false, scope: sources_scope });

            //generator.reset();

            GetSourceTypeOptions({ scope: sources_scope, variable: 'source_type_options' });
            sources_scope.source = SourceForm.fields.source['default'];
            sources_scope.sourcePathRequired = false;
            sources_scope[SourceForm.fields.source_vars.parseTypeName] = 'yaml';
            sources_scope.update_cache_timeout = 0;
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
                y = (800 > wh) ? wh - 15 : 800;
                maxrows = 18;
            } else if (ww <= 1199 && ww >= 768) {
                x = 550;
                y = (770 > wh) ? wh - 15 : 770;
                maxrows = 12;
            } else {
                x = (ww - 20);
                y = (770 > wh) ? wh - 15 : 770;
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
                title: (mode === 'edit') ? 'Edit Group' : 'Add Group',
                closeOnEscape: false,
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
                        titleHeight = dialog.find('.ui-dialog-titlebar').outerHeight(),
                        buttonHeight = dialog.find('.ui-dialog-buttonpane').outerHeight(),
                        content = dialog.find('#group-modal-dialog'),
                        w;
                    content.width(dialog.width() - 28);
                    content.css({ height: (dialog.height() - titleHeight - buttonHeight - 10) });

                    if ($('#group_tabs .active a').text() === 'Properties') {
                        textareaResize('group_variables', properties_scope);
                    }
                    else if ($('#group_tabs .active a').text() === 'Schedule') {
                        w = $('#group_tabs').width() - 18;
                        $('#schedules-overlay').width(w);
                        $('#schedules-form-container').width(w);
                        SetSchedulesInnerDialogSize();
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
                    if (properties_scope.codeMirror) {
                        properties_scope.codeMirror.destroy();
                    }
                    if (sources_scope.codeMirror) {
                        sources_scope.codeMirror.destroy();
                    }
                    $('#properties-tab').empty();
                    $('#sources-tab').empty();
                    $('#schedules-list').empty();
                    $('#schedules-form').empty();
                    $('#schedules-detail').empty();
                    $('#group-modal-dialog').hide();
                    $('#group-modal-dialog').dialog('destroy');
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
                    if (sources_scope.source && (sources_scope.source.value === 'ec2')) {
                        Wait('start');
                        ParseTypeChange({ scope: sources_scope, variable: 'source_vars', parse_variable: SourceForm.fields.source_vars.parseTypeName,
                            field_id: 'source_source_vars', onReady: waitStop });
                    } else if (sources_scope.source && (sources_scope.source.value === 'vmware')) {
                        Wait('start');
                        ParseTypeChange({ scope: sources_scope, variable: 'inventory_variables', parse_variable: SourceForm.fields.inventory_variables.parseTypeName,
                            field_id: 'source_inventory_variables', onReady: waitStop });
                    }
                    else if (sources_scope.source && (sources_scope.source.value === 'custom')) {
                        Wait('start');
                        ParseTypeChange({ scope: sources_scope, variable: 'extra_vars', parse_variable: SourceForm.fields.extra_vars.parseTypeName,
                            field_id: 'source_extra_vars', onReady: waitStop });
                    }
                }
                else if ($(e.target).text() === 'Schedule') {
                    $('#schedules-overlay').hide();
                }
            });

            if (modal_scope.groupVariablesLoadedRemove) {
                modal_scope.groupVariablesLoadedRemove();
            }
            modal_scope.groupVariablesLoadedRemove = modal_scope.$on('groupVariablesLoaded', function () {
                modal_scope.showSourceTab = (mode === 'edit' && group.has_inventory_sources && Empty(group.summary_fields.inventory_source.source)) ? false :  true;
                modal_scope.showSchedulesTab = (mode === 'edit' && sources_scope.source && sources_scope.source.value) ? true : false;
                if (mode === 'edit' && modal_scope.showSourceTab) {
                    // the use has access to the source tab, so they may create a schedule
                    GroupsScheduleListInit({ scope: modal_scope, url: schedules_url });
                }
                $('#group_tabs a:first').tab('show');
                Wait('start');
                $('#group-modal-dialog').dialog('open');
                setTimeout(function() { textareaResize('group_variables', properties_scope); }, 300);
            });


            // After the group record is loaded, retrieve related data.
            // jt-- i'm changing this to act sequentially: first load properties, then sources, then schedule
            // I accomplished this by adding "LoadSourceData" which will run the source retrieval code after the property
            // variables are set.
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
                            modal_scope.$emit('LoadSourceData');
                            //modal_scope.$emit('groupVariablesLoaded');    jt- this needs to get called after sources are loaded
                        })
                        .error(function (data, status) {
                            properties_scope.variables = null;
                            ProcessErrors(modal_scope, data, status, null, { hdr: 'Error!',
                                msg: 'Failed to retrieve group variables. GET returned status: ' + status });
                        });
                } else {
                    properties_scope.variables = "---";
                    master.variables = properties_scope.variables;
                    modal_scope.$emit('LoadSourceData');
                    //properties_scope.$emit('groupVariablesLoaded');
                }
            });


            // JT -- this gets called after the properties & properties variables are loaded, and is emitted from (groupLoaded)
            if (modal_scope.removeLoadSourceData) {
                modal_scope.removeLoadSourceData();
            }
            modal_scope.removeLoadSourceData = modal_scope.$on('LoadSourceData', function () {
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
                                }
                                // else if(fld === "source_script"){
                                //     sources_scope[fld] = data
                                // }

                                else if (data[fld] !== undefined) {
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
                            if (data.group_by && data.source === 'ec2') {
                                set = sources_scope.ec2_group_by;
                                opts = [];
                                list = data.group_by.split(',');
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
                                master.group_by = opts;
                                $('#s2id_source_group_by').select2('data', opts);
                            }
                            sources_scope.group_update_url = data.related.update;
                            modal_scope.$emit('groupVariablesLoaded');  // JT-- "groupVariablesLoaded" is where the schedule info is loaded, so I make a call after the sources_scope.source has been loaded
                            //Wait('stop');
                        })
                        .error(function (data, status) {
                            sources_scope.source = "";
                            ProcessErrors(modal_scope, data, status, null, { hdr: 'Error!',
                                msg: 'Failed to retrieve inventory source. GET status: ' + status });
                        });
                }
                else
                    modal_scope.$emit('groupVariablesLoaded');  // JT-- "groupVariablesLoaded" is where the schedule info is loaded, so I make a call after the sources_scope.source has been loaded
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

            if (modal_scope.removeChoicesComplete) {
                modal_scope.removeChoicesComplete();
            }
            modal_scope.removeChoicesComplete = modal_scope.$on('choicesCompleteGroup', function () {
                // Retrieve detail record and prepopulate the form
                Rest.setUrl(defaultUrl);
                Rest.get()
                    .success(function (data) {
                        group = data;
                        for (var fld in GroupForm.fields) {
                            if (data[fld]) {
                                properties_scope[fld] = data[fld];
                                master[fld] = properties_scope[fld];
                            }
                        }
                        schedules_url = data.related.inventory_source + 'schedules/';
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
                    if (mode === 'edit') {
                        modal_scope.$emit('choicesCompleteGroup');
                    }
                    else {
                        properties_scope.variables = "---";
                        master.variables = properties_scope.variables;
                        modal_scope.$emit('groupVariablesLoaded');
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

            Wait('start');

            if (parent_scope.removeAddTreeRefreshed) {
                parent_scope.removeAddTreeRefreshed();
            }
            parent_scope.removeAddTreeRefreshed = parent_scope.$on('GroupTreeRefreshed', function() {
                // Clean up
                Wait('stop');
                WatchInventoryWindowResize();
                if (modal_scope.searchCleanUp) {
                    modal_scope.searchCleanup();
                }
                try {
                    $('#group-modal-dialog').dialog('close');
                }
                catch(e) {
                    // ignore
                }
            });

            if (modal_scope.removeSaveComplete) {
                modal_scope.removeSaveComplete();
            }
            modal_scope.removeSaveComplete = modal_scope.$on('SaveComplete', function (e, error) {
                if (!error) {
                    modal_scope.cancelModal();
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
                    group_by,
                    data = {
                        group: group_id,
                        source: ((sources_scope.source && sources_scope.source.value) ? sources_scope.source.value : ''),
                        source_path: sources_scope.source_path,
                        credential: sources_scope.credential,
                        overwrite: sources_scope.overwrite,
                        overwrite_vars: sources_scope.overwrite_vars,
                        source_script: sources_scope.source_script,
                        update_on_launch: sources_scope.update_on_launch,
                        update_cache_timeout: (sources_scope.update_cache_timeout || 0)
                    };

                // Create a string out of selected list of regions
                regions = $('#s2id_source_source_regions').select2("data");
                r = [];
                for (i = 0; i < regions.length; i++) {
                    r.push(regions[i].id);
                }
                data.source_regions = r.join();

                if (sources_scope.source && (sources_scope.source.value === 'ec2')) {
                    data.instance_filters = sources_scope.instance_filters;
                    // Create a string out of selected list of regions
                    group_by = $('#s2id_source_group_by').select2("data");
                    r = [];
                    for (i = 0; i < group_by.length; i++) {
                        r.push(group_by[i].id);
                    }
                    data.group_by = r.join();
                }

                if (sources_scope.source && (sources_scope.source.value === 'ec2' )) {
                    // for ec2, validate variable data
                    data.source_vars = ToJSON(sources_scope.envParseType, sources_scope.source_vars, true);
                }

                if (sources_scope.source && (sources_scope.source.value === 'custom')) {
                    data.source_vars = ToJSON(sources_scope.envParseType, sources_scope.extra_vars, true);
                }

                if (sources_scope.source && (sources_scope.source.value === 'vmware')) {
                    data.source_vars = ToJSON(sources_scope.envParseType, sources_scope.inventory_variables, true);
                }

                // the API doesn't expect the credential to be passed with a custom inv script
                if(sources_scope.source.value === 'custom'){
                    delete(data.credential);
                }

                if (!parseError) {
                    Rest.setUrl(sources_scope.source_url);
                    Rest.put(data)
                        .success(function () {
                            modal_scope.$emit('SaveComplete', false);
                        })
                        .error(function (data, status) {
                            $('#group_tabs a:eq(1)').tab('show');
                            ProcessErrors(sources_scope, data, status, SourceForm, { hdr: 'Error!',
                                msg: 'Failed to update group inventory source. PUT status: ' + status });
                        });
                }
            });

            if (modal_scope.removeUpdateVariables) {
                modal_scope.removeUpdateVariables();
            }
            modal_scope.removeUpdateVariables = modal_scope.$on('updateVariables', function(e, data, url) {
                Rest.setUrl(url);
                Rest.put(data)
                    .success(function () {
                        modal_scope.$emit('formSaveSuccess');
                    })
                    .error(function (data, status) {
                        $('#group_tabs a:eq(0)').tab('show');
                        ProcessErrors(modal_scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to update group variables. PUT status: ' + status });
                    });
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
                if (parent_scope.restoreSearch) {
                    parent_scope.restoreSearch();
                }
                else {
                    Wait('stop');
                }
            };

            // Save
            modal_scope.saveGroup = function () {
                Wait('start');
                var fld, data, json_data;

                try {

                    json_data = ToJSON(properties_scope.parseType, properties_scope.variables);

                    data = {};
                    for (fld in GroupForm.fields) {
                        if (fld !== 'variables') {
                            data[fld] = properties_scope[fld];
                        }
                    }

                    data.inventory = inventory_id;

                    Rest.setUrl(defaultUrl);
                    if (mode === 'edit' || (mode === 'add' && group_created)) {
                        Rest.put(data)
                            .success(function () {
                                if (properties_scope.variables) {
                                    modal_scope.$emit('updateVariables', json_data, properties_scope.variable_url);
                                }
                                else {
                                    modal_scope.$emit('formSaveSuccess');
                                }
                            })
                            .error(function (data, status) {
                                $('#group_tabs a:eq(0)').tab('show');
                                ProcessErrors(properties_scope, data, status, GroupForm, { hdr: 'Error!',
                                    msg: 'Failed to update group: ' + group_id + '. PUT status: ' + status
                                });
                            });
                    }
                    else {
                        Rest.post(data)
                            .success(function (data) {
                                group_created = true;
                                group_id = data.id;
                                sources_scope.source_url = data.related.inventory_source;
                                if (properties_scope.variables) {
                                    modal_scope.$emit('updateVariables', json_data, data.related.variable_data);
                                }
                                else {
                                    modal_scope.$emit('formSaveSuccess');
                                }
                            })
                            .error(function (data, status) {
                                $('#group_tabs a:eq(0)').tab('show');
                                ProcessErrors(properties_scope, data, status, GroupForm, { hdr: 'Error!',
                                    msg: 'Failed to create group: ' + group_id + '. POST status: ' + status
                                });
                            });
                    }
                }
                catch(e) {
                    // ignore. ToJSON will have already alerted the user
                }
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
                parent_scope.showSchedulesTab = (mode === 'edit' &&  sources_scope.source && sources_scope.source.value) ? true : false;
                SourceChange({ scope: sources_scope, form: SourceForm });
            };

        };
    }
])

.factory('GroupsDelete', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GroupForm', 'GenerateForm',
    'Prompt', 'ProcessErrors', 'GetBasePath', 'Wait', 'BuildTree', 'Find', 'CreateDialog',
    function ($rootScope, $location, $log, $routeParams, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, Wait, BuildTree, Find, CreateDialog) {
        return function (params) {

            var scope = params.scope,
                group_id = params.group_id,
                node = Find({ list: scope.groups, key: 'id', val: group_id }),
                hosts = [],
                groups = [],
                childCount = 0,
                buttonSet;

            scope.deleteOption = "preserve-all";

            scope.helpText = "<dl><dt>Delete</dt><dd>Deletes groups and hosts associated with the group being deleted. " +
                "If a group or host is associated with other groups, it will still exist within those groups. Otherwise, " +
                "the associated groups and hosts will no longer appear in the inventory.</dd>\n" +
                "<dt style=\"margin-top: 5px;\">Promote</dt><dd>Groups and hosts associated with the group being removed will be " +
                "promoted one level. Note: groups already associated with other groups cannot be promoted to the top level of the " +
                "tree.</dd></dl>\n" +
                "<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>";

            buttonSet = [{
                label: "Cancel",
                onClick: function() {
                    scope.cancel();
                },
                icon: "fa-times",
                "class": "btn btn-default",
                "id": "group-delete-cancel-button"
            },{
                label: "Delete",
                onClick: function() {
                    scope.performDelete();
                },
                icon: "fa-check",
                "class": "btn btn-primary",
                "id": "group-delete-ok-button"
            }];

            if (scope.removeDeleteDialogReady) {
                scope.removeDeleteDialogReady();
            }
            scope.removeDeleteDialogReady = scope.$on('DeleteDialogReady', function() {
                Wait('stop');
                $('#group-delete-dialog').dialog('open');
            });

            if (scope.removeShowDeleteDialog) {
                scope.removeShowDeleteDialog();
            }
            scope.removeShowDeleteDialog = scope.$on('ShowDeleteDialog', function() {
                scope.group_name = node.name;
                scope.groupsCount = groups.length;
                scope.hostsCount = hosts.length;
                CreateDialog({
                    id: 'group-delete-dialog',
                    scope: scope,
                    buttons: buttonSet,
                    width: 650,
                    height: 350,
                    minWidth: 500,
                    title: 'Delete Group',
                    callback: 'DeleteDialogReady'
                });
            });

            if (scope.removeChildrenReady) {
                scope.removeChildrenReady();
            }
            scope.removeChildrenReady = scope.$on('ChildrenReady', function() {
                childCount++;
                if (childCount === 2) {
                    scope.$emit('ShowDeleteDialog');
                }
            });

            Wait('start');

            if (node.related.children) {
                Rest.setUrl(node.related.children);
                Rest.get()
                    .success(function(data) {
                        if (data.count) {
                            data.results.forEach(function(group) {
                                groups.push(group);
                            });
                        }
                        scope.$emit('ChildrenReady');
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to retrieve related groups. GET returned: ' + status
                        });
                    });
            }
            else {
                scope.$emit('ChildrenReady');
            }

            if (node.related.all_hosts) {
                Rest.setUrl(node.related.all_hosts);
                Rest.get()
                    .success( function(data) {
                        if (data.count) {
                            data.results.forEach(function(host) {
                                hosts.push(host);
                            });
                        }
                        scope.$emit('ChildrenReady');
                    })
                    .error( function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to retrieve related hosts. GET returned: ' + status
                        });
                    });
            }
            else {
                scope.$emit('ChildrenReady');
            }

            if (scope.removeDisassociateGroup) {
                scope.removeDisassociateGroup();
            }
            scope.removeDisassociateGroup = scope.$on('DisassociateGroup', function() {
                var data, url;
                if (!scope.selected_group_id) {
                    url = GetBasePath('inventory') + scope.inventory.id + '/groups/';
                    data = { id: node.id, disassociate: 1 };
                }
                else {
                    url = GetBasePath('groups') + node.id + '/children/';
                    data = { disassociate: 1 };
                }

                Rest.setUrl(url);
                Rest.post(data)
                    .success(function () {
                        scope.$emit('GroupDeleteCompleted'); // Signal a group refresh to start
                    })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. POST returned: ' + status
                    });
                });
            });

            if (scope.removeDeleteGroup) {
                scope.removeDeleteGroup();
            }
            scope.removeDeleteGroup = scope.$on('DeleteGroup', function() {
                var url = GetBasePath('groups') + node.id + '/';
                Rest.setUrl(url);
                Rest.destroy()
                    .success( function() {
                        scope.$emit('GroupDeleteCompleted'); // Signal a group refresh to start
                    })
                    .error( function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. DELETE returned: ' + status
                        });
                    });
            });

            scope.cancel = function() {
                $('#group-delete-dialog').dialog('close');
            };

            scope.performDelete = function() {
                $('#group-delete-dialog').dialog('close');
                Wait('start');
                if (scope.deleteOption === 'delete-all' || (scope.groupsCount === 0 && scope.hostsCount === 0)) {
                    // If user chooses Delete or there are no children, send DELETE request
                    scope.$emit('DeleteGroup');
                }
                else {
                    scope.$emit('DisassociateGroup');
                }
            };
        };
    }
])

.factory('GetRootGroups', ['Rest', 'ProcessErrors', 'GetBasePath', function(Rest, ProcessErrors, GetBasePath) {
    return function(params) {
        var scope = params.scope,
            inventory_id = params.inventory_id,
            //group_id = params.group_id,
            callback = params.callback,
            url;

        url = GetBasePath('inventory') + inventory_id + '/root_groups/';
        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                scope.$emit(callback, data.results);
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + ' failed. GET returned: ' + status });
            });
    };
}])

.factory('GroupsCopy', ['$compile', 'Rest', 'ProcessErrors', 'CreateDialog', 'GetBasePath', 'Wait', 'GenerateList', 'GroupList', 'SearchInit',
    'PaginateInit', 'GetRootGroups',
    function($compile, Rest, ProcessErrors, CreateDialog, GetBasePath, Wait, GenerateList, GroupList, SearchInit, PaginateInit, GetRootGroups) {
    return function(params) {

        var group_id = params.group_id,
            parent_scope = params.scope,
            scope = parent_scope.$new(),
            parent_group = parent_scope.selected_group_id,
            buttonSet, url, group;

        buttonSet = [{
            label: "Cancel",
            onClick: function() {
                scope.cancel();
            },
            icon: "fa-times",
            "class": "btn btn-default",
            "id": "group-copy-cancel-button"
        },{
            label: "OK",
            onClick: function() {
                scope.performCopy();
            },
            icon: "fa-check",
            "class": "btn btn-primary",
            "id": "group-copy-ok-button"
        }];

        if (scope.removeGroupsCopyPostRefresh) {
            scope.removeGroupsCopyPostRefresh();
        }
        scope.removeGroupCopyPostRefresh = scope.$on('PostRefresh', function() {
            scope.copy_groups.forEach(function(row, i) {
                scope.copy_groups[i].checked = '0';
            });
            Wait('stop');
            $('#group-copy-dialog').dialog('open');
            $('#group-copy-ok-button').attr('disabled','disabled');

            // prevent backspace from navigation when not in input or textarea field
            $(document).on("keydown", function (e) {
                if (e.which === 8 && !$(e.target).is('input[type="text"], textarea')) {
                    e.preventDefault();
                }
            });

        });

        if (scope.removeCopyDialogReady) {
            scope.removeCopyDialogReady();
        }
        scope.removeCopyDialogReady = scope.$on('CopyDialogReady', function() {
            var url = GetBasePath('inventory') + parent_scope.inventory.id + '/groups/';
            url += (parent_group) ? '?not__id__in=' + group_id + ',' + parent_group : '?not__id=' + group_id;
            GenerateList.inject(GroupList, {
                mode: 'lookup',
                id: 'copy-select-container',
                scope: scope
                //,
                //instructions: instructions
            });
            SearchInit({
                scope: scope,
                set: GroupList.name,
                list: GroupList,
                url: url
            });
            PaginateInit({
                scope: scope,
                list: GroupList,
                url: url,
                mode: 'lookup'
            });
            scope.search(GroupList.iterator);
        });

        if (scope.removeShowDialog) {
            scope.removeShowDialog();
        }
        scope.removeShowDialog = scope.$on('ShowDialog', function() {
            var d;
            scope.name = group.name;
            scope.copy_choice = "copy";
            d = angular.element(document.getElementById('group-copy-dialog'));
            $compile(d)(scope);

            CreateDialog({
                id: 'group-copy-dialog',
                scope: scope,
                buttons: buttonSet,
                width: 650,
                height: 650,
                minWidth: 600,
                title: 'Copy or Move Group',
                callback: 'CopyDialogReady',
                onClose: function() {
                    scope.cancel();
                }
            });
        });

        if (scope.removeRootGroupsReady) {
            scope.removeRootGroupsReady();
        }
        scope.removeRootGroupsReady = scope.$on('RootGroupsReady', function(e, root_groups) {
            scope.offer_root_group = true;
            scope.use_root_group = false;
            root_groups.every(function(row) {
                if (row.id === group_id) {
                    scope.offer_root_group = false;
                    return false;
                }
                return true;
            });
            url = GetBasePath('groups') + group_id + '/';
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    group = data;
                    scope.$emit('ShowDialog');
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. GET returned: ' + status });
                });
        });

        Wait('start');

        GetRootGroups({
            scope: scope,
            group_id: group_id,
            inventory_id: parent_scope.inventory.id,
            callback: 'RootGroupsReady'
        });

        scope.cancel = function() {
            $(document).off("keydown");
            try {
                $('#group-copy-dialog').dialog('close');
            }
            catch(e) {
                // ignore
            }
            scope.searchCleanup();
            parent_scope.restoreSearch();
            scope.$destroy();
        };

        scope['toggle_' + GroupList.iterator] = function (id) {
            var count = 0,
                list = GroupList;
            scope[list.name].forEach( function(row, i) {
                if (row.id === id) {
                    if (row.checked === '0') {
                        scope[list.name][i].checked = '1';
                        scope[list.name][i].success_class = 'success';
                    }
                    else {
                        scope[list.name][i].checked = '0';
                        scope[list.name][i].success_class = '';
                    }
                } else {
                    scope[list.name][i].checked = '0';
                    scope[list.name][i].success_class = '';
                }
            });
            // Check if any rows are checked
            scope[list.name].forEach(function(row) {
                if (row.checked === '1') {
                    count++;
                }
            });
            if (count === 0) {
                $('#group-copy-ok-button').attr('disabled','disabled');
            }
            else {
                $('#group-copy-ok-button').removeAttr('disabled');
            }
        };

        scope.toggleUseRootGroup = function() {
            var list = GroupList;
            //console.log("scope.use_root_group: " + scope.use_root_group);
            if (scope.use_root_group) {
                $('#group-copy-ok-button').removeAttr('disabled');
            }
            else {
                // check for group selection
                $('#group-copy-ok-button').attr('disabled','disabled');
                scope[list.name].every(function(row) {
                    if (row.checked === '1') {
                        $('#group-copy-ok-button').removeAttr('disabled');
                        return false;
                    }
                    return true;
                });
            }
        };

        scope.performCopy = function() {
            var list = GroupList,
                target,
                url;

            Wait('start');

            if (scope.use_root_group) {
                target = null;
            }
            else {
                scope[list.name].every(function(row) {
                    if (row.checked === '1') {
                        target = row;
                        return false;
                    }
                    return true;
                });
            }

            if (scope.copy_choice === 'move') {
                // Respond to move

                // disassociate the group from the original parent
                if (scope.removeGroupRemove) {
                    scope.removeGroupRemove();
                }
                scope.removeGroupRemove = scope.$on('RemoveGroup', function () {
                    if (parent_group > 0) {
                        // Only remove a group from a parent when the parent is a group and not the inventory root
                        url = GetBasePath('groups') + parent_group + '/children/';
                        Rest.setUrl(url);
                        Rest.post({ id: group.id, disassociate: 1 })
                            .success(function () {
                                scope.cancel();
                            })
                            .error(function (data, status) {
                                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                    msg: 'Failed to remove ' + group.name + ' from group ' + parent_group + '. POST returned: ' + status });
                            });
                    } else {
                        scope.cancel();
                    }
                });

                // add the new group to the target
                url = (target) ?
                    GetBasePath('groups') + target.id + '/children/' :
                    GetBasePath('inventory') + parent_scope.inventory.id + '/groups/';
                group = {
                    id: group.id,
                    name: group.name,
                    description: group.description,
                    inventory: parent_scope.inventory.id
                };
                Rest.setUrl(url);
                Rest.post(group)
                    .success(function () {
                        scope.$emit('RemoveGroup');
                    })
                    .error(function (data, status) {
                        var target_name = (target) ? target.name : 'inventory';
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to add ' + group.name + ' to ' + target_name + '. POST returned: ' + status });
                    });
            }
            else {
                // Respond to copy by adding the new group to the target
                url = (target) ?
                      GetBasePath('groups') + target.id + '/children/' :
                      GetBasePath('inventory') + parent_scope.inventory.id + '/groups/';

                group = {
                    id: group.id,
                    name: group.name,
                    description: group.description,
                    inventory: parent_scope.inventory.id
                };

                Rest.setUrl(url);
                Rest.post(group)
                    .success(function () {
                        scope.cancel();
                    })
                    .error(function (data, status) {
                        var target_name = (target) ? target.name : 'inventory';
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to add ' + group.name + ' to ' + target_name + '. POST returned: ' + status
                        });
                    });
            }
        };

    };
}])

.factory('ShowUpdateStatus', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GenerateForm',
    'Prompt', 'ProcessErrors', 'GetBasePath', 'FormatDate', 'InventoryStatusForm', 'Wait',
    function ($rootScope, $location, $log, $routeParams, Rest, Alert, GenerateForm, Prompt, ProcessErrors, GetBasePath,
        FormatDate, InventoryStatusForm, Wait) {
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
                        //WatchInventoryWindowResize();
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
