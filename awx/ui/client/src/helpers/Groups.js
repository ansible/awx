/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

'use strict';

/**
 * @ngdoc function
 * @name helpers.function:Groups
 * @description    inventory tree widget add/edit/delete
*/

import listGenerator from '../shared/list-generator/main';

export default
angular.module('GroupsHelper', [ 'RestServices', 'Utilities', listGenerator.name, 'GroupListDefinition', 'SearchHelper',
               'PaginationHelpers', listGenerator.name, 'GroupsHelper', 'InventoryHelper', 'SelectionHelper',
               'JobSubmissionHelper', 'RefreshHelper', 'PromptDialog', 'CredentialsListDefinition',
                'InventoryStatusDefinition', 'VariablesHelper', 'SchedulesListDefinition', 'StandardOutHelper',
               'SchedulesHelper'
])

/**
 *
 * Lookup options for group source and build an array of drop-down choices
 *
 */
.factory('GetSourceTypeOptions', ['Rest', 'ProcessErrors', 'GetBasePath',
         function (Rest, ProcessErrors, GetBasePath) {
             return function (params) {
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
                                     label: choices[i][1],
                                     value: choices[i][0]
                                 });
                             }
                         }
                         scope.cloudCredentialRequired = false;
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

/**
 *
 * TODO: Document
 *
 */
.factory('ViewUpdateStatus', ['$state', 'Rest', 'ProcessErrors', 'GetBasePath', 'Alert', 'Wait', 'Empty', 'Find',
         function ($state, Rest, ProcessErrors, GetBasePath, Alert, Wait, Empty, Find) {
             return function (params) {

                 var scope = params.scope,
                 group_id = params.group_id,
                 group = Find({ list: scope.groups, key: 'id', val: group_id });

                 if (scope.removeSourceReady) {
                     scope.removeSourceReady();
                 }
                 scope.removeSourceReady = scope.$on('SourceReady', function(e, source) {

                    // Get the ID from the correct summary field
                    var update_id = (source.current_update) ? source.summary_fields.current_update.id : source.summary_fields.last_update.id;

                    $state.go('inventorySyncStdout', {id: update_id});

                 });

                 if (group) {
                     if (Empty(group.source)) {
                         // do nothing
                     } else if (Empty(group.status) || group.status === "never updated") {
                         Alert('No Status Available', 'An inventory sync has not been performed for the selected group. Start the process by ' +
                               'clicking the <i class="fa fa-refresh"></i> button.', 'alert-info', null, null, null, null, true);
                     } else {
                         Wait('start');
                         Rest.setUrl(group.related.inventory_source);
                         Rest.get()
                         .success(function (data) {
                             scope.$emit('SourceReady', data);
                         })
                         .error(function (data, status) {
                             ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                           msg: 'Failed to retrieve inventory source: ' + group.related.inventory_source +
                                               ' GET returned status: ' + status });
                         });
                     }
                 }

             };
         }
])

/**
 *
 * TODO: Document
 *
 */
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

/**
 *
 * TODO: Document
 *
 */
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
                     status_tip = 'Sync not performed. Click <i class="fa fa-refresh"></i> to start it now.';
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

/**
 *
 * Cancel a pending or running inventory sync
 *
 */
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
 * Deprecated factory that used to support /#/home/groups/
 *
 */
.factory('GroupsEdit', ['$filter', '$rootScope', '$location', '$log', '$stateParams', '$compile', 'Rest', 'Alert', 'GroupForm', 'GenerateForm',
         'Prompt', 'ProcessErrors', 'GetBasePath', 'SetNodeName', 'ParseTypeChange', 'GetSourceTypeOptions', 'InventoryUpdate',
         'LookUpInit', 'Empty', 'Wait', 'GetChoices', 'UpdateGroup', 'SourceChange', 'Find',
         'ParseVariableString', 'ToJSON', 'GroupsScheduleListInit', 'SetSchedulesInnerDialogSize', 'CreateSelect2',
         function ($filter, $rootScope, $location, $log, $stateParams, $compile, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
                   GetBasePath, SetNodeName, ParseTypeChange, GetSourceTypeOptions, InventoryUpdate, LookUpInit, Empty, Wait,
                   GetChoices, UpdateGroup, SourceChange, Find, ParseVariableString, ToJSON, GroupsScheduleListInit,
                   SetSchedulesInnerDialogSize, CreateSelect2) {
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

                           var form_scope =
                           generator.inject(GroupForm, { mode: mode, id: 'properties-tab', related: false, scope: properties_scope });
                           var source_form_scope =
                           generator.inject(GroupForm, { mode: mode, id: 'sources-tab', related: false, scope: sources_scope });

                           //generator.reset();

                           GetSourceTypeOptions({ scope: sources_scope, variable: 'source_type_options' });
                           sources_scope.source = GroupForm.fields.source['default'];
                           sources_scope.sourcePathRequired = false;
                           sources_scope[GroupForm.fields.source_vars.parseTypeName] = 'yaml';
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

                           function initSourceChange() {
                               parent_scope.showSchedulesTab = (mode === 'edit' &&  sources_scope.source && sources_scope.source.value!=="manual") ? true : false;
                               SourceChange({ scope: sources_scope, form: GroupForm });
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
                                   'Save': function () {
                                       modal_scope.saveGroup();
                                   },
                                   'Cancel': function() {
                                       modal_scope.cancelModal();
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
                                   function updateButtonStatus(isValid) {
                               $('.ui-dialog[aria-describedby="group-modal-dialog"]').find('.btn-primary').prop('disabled', !isValid);
                                   }
                           form_scope.$watch('group_form.$valid', updateButtonStatus);
                           source_form_scope.$watch('source_form.$valid', updateButtonStatus);
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
                                       ParseTypeChange({ scope: sources_scope, variable: 'source_vars', parse_variable: GroupForm.fields.source_vars.parseTypeName,
                                                       field_id: 'source_source_vars', onReady: waitStop });
                                   } else if (sources_scope.source && (sources_scope.source.value === 'vmware' ||
                                                                       sources_scope.source.value === 'openstack')) {
                                       Wait('start');
                                       ParseTypeChange({ scope: sources_scope, variable: 'inventory_variables', parse_variable: GroupForm.fields.inventory_variables.parseTypeName,
                                                       field_id: 'source_inventory_variables', onReady: waitStop });
                                   }
                                   else if (sources_scope.source && (sources_scope.source.value === 'custom')) {
                                       Wait('start');
                                       ParseTypeChange({ scope: sources_scope, variable: 'extra_vars', parse_variable: GroupForm.fields.extra_vars.parseTypeName,
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
                              if (mode === 'edit' &&
                                  group.has_inventory_sources &&
                                  Empty(group.summary_fields.inventory_source.source) &&
                                  sources_scope.source &&
                                  sources_scope.source.value !== 'manual') {
                                  modal_scope.showSourceTab = false;
                              } else {
                                  modal_scope.showSourceTab = true;
                              }
                               modal_scope.showSchedulesTab = (mode === 'edit' && sources_scope.source && sources_scope.source.value!=='manual') ? true : false;
                               if (mode === 'edit' && modal_scope.showSourceTab) {
                                   // the use has access to the source tab, so they may create a schedule
                                   GroupsScheduleListInit({ scope: modal_scope, url: schedules_url });
                               }
                               $('#group_tabs a:first').tab('show');
                               Wait('start');
                               $('#group-modal-dialog').dialog('open');
                               setTimeout(function() { textareaResize('group_variables', properties_scope); }, 300);
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
                                       form = GroupForm;
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
                                               data.source = (data.source === "" ) ? "manual" : data.source;
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
                                           }
                                           else if(fld === "inventory_script"){
                                               // the API stores it as 'source_script', we call it inventory_script
                                               data.summary_fields.inventory_script = data.summary_fields.source_script;
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
                                                               id: set[j].value,
                                                               text: set[j].label
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
                                                           id: set[j].value,
                                                           text: set[j].label
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
                                       modal_scope.$emit('groupVariablesLoaded');  // JT-- "groupVariablesLoaded" is where the schedule info is loaded, so I make a call after the sources_scope.source has been loaded
                                       //Wait('stop');
                                   })
                                   .error(function (data, status) {
                                       sources_scope.source = "";
                                       ProcessErrors(modal_scope, data, status, null, { hdr: 'Error!',
                                                     msg: 'Failed to retrieve inventory source. GET status: ' + status });
                                   });
                               }
                               else {
                                   modal_scope.$emit('groupVariablesLoaded');  // JT-- "groupVariablesLoaded" is where the schedule info is loaded, so I make a call after the sources_scope.source has been loaded
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
                                   modal_scope.$emit('LoadSourceData');
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
                               CreateSelect2({
                                   element: '#source_source',
                                   multiple: false
                               });
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
                                   source: ((sources_scope.source && sources_scope.source.value!=='manual') ? sources_scope.source.value : ''),
                                   source_path: sources_scope.source_path,
                                   credential: sources_scope.credential,
                                   overwrite: sources_scope.overwrite,
                                   overwrite_vars: sources_scope.overwrite_vars,
                                   source_script: sources_scope.inventory_script,
                                   update_on_launch: sources_scope.update_on_launch,
                                   update_cache_timeout: (sources_scope.update_cache_timeout || 0)
                               };

                               // Create a string out of selected list of regions
                               if(sources_scope.source_regions){
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

                               if (sources_scope.source && (sources_scope.source.value === 'ec2' )) {
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
                               if(sources_scope.source && sources_scope.source.value === 'custom'){
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
                                       ProcessErrors(sources_scope, data, status, GroupForm, { hdr: 'Error!',
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

                                   json_data = ToJSON(properties_scope.parseType, properties_scope.variables, true);

                                   data = {};
                                   for (fld in GroupForm.fields) {
                                       data[fld] = properties_scope[fld];
                                   }

                                   data.inventory = inventory_id;

                                   Rest.setUrl(defaultUrl);
                                   if (mode === 'edit' || (mode === 'add' && group_created)) {
                                       Rest.put(data)
                                       .success(function () {
                                           modal_scope.$emit('formSaveSuccess');
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
                                           modal_scope.$emit('formSaveSuccess');
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
                           sources_scope.sourceChange = function () {
                               sources_scope.credential_name = "";
                               sources_scope.credential = "";
                               if (sources_scope.credential_name_api_error) {
                                   delete sources_scope.credential_name_api_error;
                               }
                               initSourceChange();
                           };

                       };
                   }
]);
