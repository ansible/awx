/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  GroupsHelper
 *
 *  Routines that handle group add/edit/delete on the Inventory tree widget.
 *
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
                tree_id = params.tree_id,
                group = Find({ list: scope.groups, key: 'id', val: tree_id });

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
                    tip = "Group contains 0 hosts.";
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
                case '':
                    launch_class = 'btn-disabled';
                    stat = 'n/a';
                    stat_class = 'na';
                    status_tip = 'Cloud source not configured. Click <i class="fa fa-pencil"></i> to update.';
                    launch_tip = 'Cloud source not configured.';
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
                    $('#source_form').removeClass('squeeze');
                } else if (scope.source.value === 'ec2') {
                    scope.source_region_choices = scope.ec2_regions;
                    //$('#s2id_group_source_regions').select2('data', []);
                    $('#s2id_source_source_regions').select2('data', [{
                        id: 'all',
                        text: 'All'
                    }]);
                    $('#source_form').addClass('squeeze');
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

/**
 * 
 * Add the list of schedules to the Group Edit modal
 *
 */
.factory('ScheduleList', ['ScheduleEdit', 'SchedulesList', 'GenerateList', 'SearchInit', 'PaginateInit', 'Rest', 'PageRangeSetup',
'Wait', 'ProcessErrors', 'Find', 'ToggleSchedule', 'DeleteSchedule', 'GetBasePath', 'SchedulesListInit',
function(ScheduleEdit, SchedulesList, GenerateList, SearchInit, PaginateInit, Rest, PageRangeSetup, Wait, ProcessErrors, Find,
ToggleSchedule, DeleteSchedule, GetBasePath, SchedulesListInit) {
    return function(params) {
        var parent_scope = params.scope,
            url = params.url,
            schedule_scope = parent_scope.$new(),
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

        if (schedule_scope.removePostRefresh) {
            schedule_scope.removePostRefresh();
        }
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
        
        parent_scope.refreshSchedule = function() {
            schedule_scope.search(list.iterator);
        };

        schedule_scope.editSchedule = function(id) {
            ScheduleEdit({ scope: parent_scope, mode: 'edit', url: GetBasePath('schedules') + id + '/' });
        };

        schedule_scope.addSchedule = function() {
            ScheduleEdit({ scope: parent_scope, mode: 'add', url: url });
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
.factory('ScheduleEdit', ['SchedulerInit', 'Rest', 'Wait', 'SetSchedulesInnerDialogSize', 'SchedulePost', 'ProcessErrors',
function(SchedulerInit, Rest, Wait, SetSchedulesInnerDialogSize, SchedulePost, ProcessErrors) {
    return function(params) {
        var parent_scope = params.scope,
            mode = params.mode,  // 'create' or 'edit'
            url = params.url,
            scope = parent_scope.$new(),
            schedule = {},
            scheduler,
            target,
            showForm,
            list,
            detail,
            restoreList,
            container;

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

        if (scope.removeScheduleReady) {
            scope.removeScheduleReady();
        }
        scope.removeScheduleReady = scope.$on('ScheduleReady', function() {
            // Insert the scheduler widget into the hidden div
            scheduler = SchedulerInit({ scope: scope, requireFutureStartTime: false });
            scheduler.inject('schedules-form', false);
            scheduler.injectDetail('schedules-detail', false);
            scheduler.clear();
            scope.showRRuleDetail = false;
            parent_scope.schedulesTitle = (mode === 'edit') ? 'Edit Schedule' : 'Create Schedule';
        
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
            parent_scope.refreshSchedule();
        };

        parent_scope.showScheduleDetail = function() {
            if (parent_scope.formShowing) {
                if (scheduler.isValid()) {
                    detail.width($('#schedules-form').width()).height($('#schedules-form').height());
                    target.hide();
                    detail.show();
                    parent_scope.formShowing = false;
                }
            }
            else {
                detail.hide();
                target.show();
                parent_scope.formShowing = true;
            }
        };

        if (scope.removeScheduleSaved) {
            scope.removeScheduleSaved();
        }
        scope.removeScheduleSaved = scope.$on('ScheduleSaved', function() {
            Wait('stop');
            container.hide('slide', { direction: 'right' }, 500, restoreList);
        });
        
        parent_scope.saveScheduleForm = function() {
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

        parent_scope.cancelScheduleForm = function() {
            container.hide('slide', { direction: 'right' }, 500, restoreList);
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


.factory('GroupsEdit', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GroupForm', 'GenerateForm',
    'Prompt', 'ProcessErrors', 'GetBasePath', 'SetNodeName', 'ParseTypeChange', 'GetSourceTypeOptions', 'InventoryUpdate',
    'LookUpInit', 'Empty', 'Wait', 'GetChoices', 'UpdateGroup', 'SourceChange', 'Find','WatchInventoryWindowResize',
    'ParseVariableString', 'ToJSON', 'ScheduleList', 'SourceForm', 'SetSchedulesInnerDialogSize', 'BuildTree',
    function ($rootScope, $location, $log, $routeParams, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, SetNodeName, ParseTypeChange, GetSourceTypeOptions, InventoryUpdate, LookUpInit, Empty, Wait,
        GetChoices, UpdateGroup, SourceChange, Find, WatchInventoryWindowResize, ParseVariableString, ToJSON, ScheduleList,
        SourceForm, SetSchedulesInnerDialogSize, BuildTree) {
        return function (params) {

            var parent_scope = params.scope,
                group_id = params.group_id,
                tree_id = params.tree_id,
                mode = params.mode,  // 'add' or 'edit'
                inventory_id = params.inventory_id,
                groups_reload = params.groups_reload,
                callback = params.callback,
                generator = GenerateForm,
                defaultUrl,
                master = {},
                choicesReady,
                modal_scope = parent_scope.$new(),
                properties_scope = parent_scope.$new(),
                sources_scope = parent_scope.$new(),
                x, y, ww, wh, maxrows,
                schedules_url = '';
            
            if (mode === 'edit') {
                defaultUrl = GetBasePath('groups') + group_id + '/';
            }
            else {
                defaultUrl = (group_id !== null) ? GetBasePath('groups') + group_id + '/children/' :
                    GetBasePath('inventory') + inventory_id + '/groups/';
            }

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
                title: 'Edit Group',
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
                    $('#group-modal-dialog').hide();
                    $('#group-modal-dialog').dialog('destroy');
                    $('#properties-tab').empty();
                    $('#sources-tab').empty();
                    $('#schedules-list').empty();
                    $('#schedules-form').empty();
                    $('#schedules-detail').empty();
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
                    $('#schedules-overlay').hide();
                    parent_scope.formShowing = true;
                    ScheduleList({ scope: parent_scope, url: schedules_url });
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
                    parent_scope.showSourceTab = false;
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

            Wait('start');

            if (parent_scope.removeAddTreeRefreshed) {
                parent_scope.removeAddTreeRefreshed();
            }
            parent_scope.removeAddTreeRefreshed = parent_scope.$on('GroupTreeRefreshed', function() {
                //Clean up
                if (modal_scope.searchCleanUp) {
                    modal_scope.searchCleanup();
                }
                try {
                    $('#group-modal-dialog').dialog('close');
                }
                catch(e) {
                    // ignore
                }
                // Change the selected group
                if (groups_reload && parent_scope.selected_tree_id !== tree_id) {
                    parent_scope.showHosts(tree_id, group_id, false);
                } else {
                    Wait('stop');
                }
                WatchInventoryWindowResize();
                parent_scope.removeAddTreeRefreshed();
            });

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
                    } else if (callback) {
                        try {
                            $('#group-modal-dialog').dialog('close');
                        }
                        catch(err) {
                            //ignore
                        }
                        parent_scope.$emit(callback);
                    } else {
                        if (mode === 'add') {
                            BuildTree({
                                scope: parent_scope,
                                inventory_id: inventory_id,
                                refresh: true,
                                new_group_id: group_id
                            });
                        }
                        else {
                            parent_scope.$emit('GroupTreeRefreshed');
                        }
                    }
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
                if (callback) {
                    parent_scope.$emit(callback);
                }
                else {
                    if (modal_scope.searchCleanup) {
                        modal_scope.searchCleanup();
                    }
                    WatchInventoryWindowResize();
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
                    if (mode === 'edit') {
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
                                Wait('stop');
                                ProcessErrors(properties_scope, data, status, GroupForm, { hdr: 'Error!',
                                    msg: 'Failed to update group: ' + group_id + '. PUT status: ' + status
                                });
                            });
                    }
                    else {
                        Rest.post(data)
                            .success(function (data) {
                                if (properties_scope.variables) {
                                    sources_scope.source_url = data.related.inventory_source;
                                    modal_scope.$emit('updateVariables', json_data, data.related.variable_data);
                                }
                                else {
                                    modal_scope.$emit('formSaveSuccess');
                                }
                            })
                            .error(function (data, status) {
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
                parent_scope.showSourceTab = (sources_scope.source && sources_scope.source.value) ? true : false;
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
                body: '<div class=\"alert alert-info\">Are you sure you want to delete group <em>' + node.name + '?</div>',
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