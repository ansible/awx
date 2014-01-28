/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  GroupsHelper
 *
 *  Routines that handle group add/edit/delete on the Inventory tree widget.
 *  
 */

'use strict';

angular.module('GroupsHelper', [ 'RestServices', 'Utilities', 'ListGenerator', 'GroupListDefinition',
                                 'SearchHelper', 'PaginationHelpers', 'ListGenerator', 'AuthService', 'GroupsHelper',
                                 'InventoryHelper', 'SelectionHelper', 'JobSubmissionHelper', 'RefreshHelper',
                                 'PromptDialog', 'InventorySummaryHelpDefinition', 'CredentialsListDefinition',
                                 'InventoryTree'
                                 ])

    .factory('GetSourceTypeOptions', [ 'Rest', 'ProcessErrors', 'GetBasePath', function(Rest, ProcessErrors, GetBasePath) {
        return function(params) {
            // Lookup options for source and build an array of drop-down choices
            var scope = params.scope;
            var variable = params.variable;
            if (scope[variable] == undefined) {
                scope[variable] = [];
                Rest.setUrl(GetBasePath('inventory_sources'));
                Rest.options()
                    .success( function(data, status, headers, config) { 
                        var choices = data.actions.GET.source.choices
                        for (var i=0; i < choices.length; i++) {
                            if (choices[i][0] !== 'file') {
                                scope[variable].push({ 
                                    label: ( (choices[i][0] == '') ? 'Manual' : choices[i][1] ),
                                    value: choices[i][0]
                                    });
                            }
                        }
                        })
                    .error( function(data, status, headers, config) { 
                        ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Failed to retrieve options for inventory_sources.source. OPTIONS status: ' + status });
                    });
            }
        }
        }])


    .factory('GetUpdateIntervalOptions', [ function() {
        return function() {
            return [
                { label: 'none', value: 0 },
                { label: '5 minutes', value: 5 },
                { label: '10 minutes', value: 10 },
                { label: '15 minutes', value: 15 },
                { label: '30 minutes', value: 30 },
                { label: '45 minutes', value: 45 },
                { label: '1 hour', value: 60 },
                { label: '2 hours', value: 120 }, 
                { label: '3 hours', value: 180 },
                { label: '4 hours', value: 240 },
                { label: '5 hours', value: 300 },
                { label: '6 hours', value: 360 },
                { label: '7 hours', value: 420 },
                { label: '8 hours', value: 480 },
                { label: '9 hours', value: 540 },
                { label: '10 hours', value: 600 },
                { label: '11 hours', value: 660 },
                { label: '12 hours', value: 720 },
                { label: '13 hours', value: 780 },
                { label: '14 hours', value: 840 },
                { label: '15 hours', value: 900 },
                { label: '16 hours', value: 960 },
                { label: '17 hours', value: 1020 },
                { label: '18 hours', value: 1080 },
                { label: '19 hours', value: 1140},
                { label: '20 hours', value: 1200 },
                { label: '21 hours', value: 1260 },
                { label: '22 hours', value: 1320 },
                { label: '23 hours', value: 1380 },
                { label: '24 hours', value: 1440 },
                { label: '48 hours', value: 1880 },
                { label: '72 hours', value: 4320 },
                { label: 'weekly (every 7 days)', value: 10080 },
                { label: 'monthly (every 30 days)', value: 43200 }
                ];
        }
        }])
    
    .factory('ViewUpdateStatus', [ 'Rest', 'ProcessErrors', 'GetBasePath', 'ShowUpdateStatus', 'Alert', 'Wait', 'Empty', 'Find',
    function(Rest, ProcessErrors, GetBasePath, ShowUpdateStatus, Alert, Wait, Empty, Find) {
        return function(params) {
        
        var scope = params.scope;
        var tree_id = params.tree_id;
        var group_id = params.group_id;
        var found = false;
        var group = Find({ list: scope.groups, key: 'id', val: tree_id });
        
        if (group) {
           if (Empty(group.source)) {
              Alert('Missing Configuration', 'The selected group is not configured for inventory sync. ' +
                  'You must first edit the group, provide Source settings, and then run the sync process.', 'alert-info');
           }
           else if (Empty(group.status) || group.status == "never updated") {
              Alert('No Status Available', 'An inventory sync has not been performed for the selected group. Start the process by ' +
                  'clicking the <i class="fa fa-exchange"></i> button.', 'alert-info');
           }
           else {
              Wait('start');
              Rest.setUrl(group.related.inventory_source);
              Rest.get()
                  .success( function(data, status, headers, config) {
                      var url = (data.related.current_update) ? data.related.current_update : data.related.last_update;
                      ShowUpdateStatus({ 
                          group_name: data.summary_fields.group.name,
                          last_update: url,
                          license_error: ( (data.summary_fields.last_update && data.summary_fields.last_update.license_error) ? true : false ),
                          tree_id: tree_id,
                          group_id: group_id,
                          parent_scope: scope
                          });
                      })
                  .error( function(data, status, headers, config) {
                      Wait('stop');
                      ProcessErrors(scope, data, status, form,
                          { hdr: 'Error!', msg: 'Failed to retrieve inventory source: ' + group.related.inventory_source + 
                          ' POST returned status: ' + status });
                      });
           }
        }

        }
        }])
    
    .factory('GetHostsStatusMsg', [ function() {
    return function(params) {  
        
        var active_failures = params.active_failures; 
        var total_hosts = params.total_hosts;
        var inventory_id = params.inventory_id;
        var group_id = params.group_id;

        var tip, failures, html_class;

        // Return values for use on host status indicator
        
        if (active_failures > 0) {
            tip = total_hosts + ( (total_hosts == 1) ? ' host' : ' hosts' ) + '. ' + active_failures + ' with failed jobs.';
            html_class = 'true';
            failures = true;
        }
        else {
           failures = false;
           if (total_hosts == 0) {
               // no hosts
               tip = "Group contains 0 hosts.";
               html_class = 'na';
           }
           else {
               // many hosts with 0 failures
               tip = total_hosts + ( (total_hosts == 1) ? ' host' : ' hosts' ) + '. No job failures';
               html_class = 'false';
           }
        }

        return { tooltip: tip, failures: failures, 'class': html_class };
        
        }
        }])

    .factory('GetSyncStatusMsg', [ function() {
    return function(params) {  
        
        var status = params.status;

        var launch_class = '';
        var launch_tip = 'Start sync process';        
        var stat, stat_class, status_tip;
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
                launch_class = 'btn-disabled',
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
            }

        }
        }])

    .factory('SourceChange', [ 'GetBasePath', 'CredentialList', 'LookUpInit', 'Empty',
    function(GetBasePath, CredentialList, LookUpInit, Empty){
    return function(params) {
        
        var scope = params.scope; 
        var form = params.form;
        
        if (!Empty(scope['source'])) {
            if (scope['source'].value == 'file') {
                scope.sourcePathRequired = true;
            }
            else {
                scope.sourcePathRequired = false;
                // reset fields
                scope.source_path = '';
                scope[form.name + '_form']['source_path'].$setValidity('required',true);
            }
            if (scope['source'].value == 'rax') {
                scope['source_region_choices'] = scope['rax_regions'];
                //$('#s2id_group_source_regions').select2('data', []);
                $('#s2id_group_source_regions').select2('data', [{ id: 'all', text: 'All' }]);
            }
            else if (scope['source'].value == 'ec2') {
                scope['source_region_choices'] = scope['ec2_regions'];
                //$('#s2id_group_source_regions').select2('data', []);
                $('#s2id_group_source_regions').select2('data', [{ id: 'all', text: 'All' }]);
            }
            if (scope['source'].value == 'rax' || scope['source'].value == 'ec2') {
                var kind = (scope.source.value == 'rax') ? 'rax' : 'aws';
                var url = GetBasePath('credentials') + '?cloud=true&kind=' + kind;  
                LookUpInit({
                    url: url, 
                    scope: scope,
                    form: form,
                    list: CredentialList,
                    field: 'credential' 
                    });
            }
        }
        
        } 
        }])

    
    // Cancel a pending or running inventory sync
    .factory('GroupsCancelUpdate', ['Rest', 'ProcessErrors', 'Alert', 'Wait', 'Find',
    function(Rest, ProcessErrors, Alert, Wait, Find) {
    return function(params) {
        
        var scope = params.scope;
        var id = params.tree_id;

        if (scope.removeCancelUpdate) {
           scope.removeCancelUpdate();
        }
        scope.removeCancelUpdate = scope.$on('CancelUpdate', function(e, url) {
            // Cancel the update process
            Rest.setUrl(url)
            Rest.post()
                .success( function(data, status, headers, config) {
                    Wait('stop');
                    Alert('Inventory Sync Cancelled', 'Your request to cancel the sync process was submitted to the task manger. ' +
                        'Click the <i class="fa fa-refresh fa-lg"></i> button to monitor the status.', 'alert-info');        
                    })
                .error( function(data, status, headers, config) {
                    Wait('stop');
                    ProcessErrors(scope, data, status, null,
                        { hdr: 'Error!', msg: 'Call to ' + url + ' failed. POST status: ' + status });
                    });  
            });

        if (scope.removeCheckCancel) {
           scope.removeCheckCancel();
        }
        scope.removeCheckCancel = scope.$on('CheckCancel', function(e, last_update, current_update) {
            // Check that we have access to cancelling an update
            var url = (current_update) ? current_update : last_update;
            url += 'cancel/';
            Rest.setUrl(url);
            Rest.get()
                .success( function(data, status, headers, config) {
                    if (data.can_cancel) {
                        scope.$emit('CancelUpdate', url);
                    }
                    else {
                        Wait('stop');
                        Alert('Cancel Inventory Sync', 'Either you do not have access or the sync process completed.<br /> ' + 
                            'Click the <i class="fa fa-refresh fa-lg"></i> button to view the latest status.', 'alert-info');
                    }
                    })
                .error( function(data, status, headers, config) {
                    Wait('stop');
                    ProcessErrors(scope, data, status, null,
                        { hdr: 'Error!', msg: 'Call to ' + url + ' failed. GET status: ' + status });
                    });
            });

        // Cancel the update process
        var group = Find({ list: scope.groups, key: 'id', val: id });
        scope.selected_tree_id = group.id;
        scope.selected_group_id = group.group_id;
        
        if (group && (group.status == 'updating' || group.status == 'pending')) {
            // We found the group, and there is a running update
            Wait('start');
            Rest.setUrl(group.related.inventory_source);
            Rest.get()
                .success( function(data, status, headers, config) {
                    scope.$emit('CheckCancel', data.related.last_update, data.related.current_update);
                    })
                .error( function(data, status, headers, config) {
                    Wait('stop');
                    ProcessErrors(scope, data, status, null,
                        { hdr: 'Error!', msg: 'Call to ' + group.related.inventory_source + ' failed. GET status: ' + status });
                    });
        }
        else {
            Alert('Cancel Inventory Sync', 'The sync process completed. Click the <i class="fa fa-refresh fa-lg"></i> to' +
                  ' view the latest status.', 'alert-info');
        }
      
        }
        }])

    .factory('GroupsAdd', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GroupForm', 'GenerateForm', 
        'Prompt', 'ProcessErrors', 'GetBasePath', 'ParseTypeChange', 'GroupsEdit', 'Wait', 'GetChoices',
        'GetSourceTypeOptions', 'LookUpInit', 'BuildTree', 'SourceChange',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, ParseTypeChange, GroupsEdit, Wait, GetChoices, GetSourceTypeOptions, LookUpInit, BuildTree,
        SourceChange) {
    return function(params) {

        var inventory_id = params.inventory_id;
        var group_id = (params.group_id !== undefined) ? params.group_id : null;
        var parent_scope = params.scope;
       
        // Inject dynamic view
        var defaultUrl = (group_id !== null) ? GetBasePath('groups') + group_id + '/children/' : 
            GetBasePath('inventory') + inventory_id + '/groups/';
        var form = GroupForm;
        var generator = GenerateForm;
        var scope = generator.inject(form, { mode: 'add', modal: true, related: false, show_modal: false });
        var groupCreated = false;

        $('#form-modal .btn-none').removeClass('btn-none').addClass('btn-success');

        scope.formModalActionLabel = 'Save';
        scope.formModalCancelShow = true;
        scope.parseType = 'yaml';
        scope.source = null;
        ParseTypeChange(scope);
        
        generator.reset();
        var master={};

        if (scope.removeAddTreeRefreshed) {
            scope.removeAddTreeRefreshed();
        }
        scope.removeAddTreeRefreshed = scope.$on('GroupTreeRefreshed', function(e) {
            $rootScope.formModalHeader = null; 
            $rootScope.formModalCancleShow= null; 
            $rootScope.formModalActionLabel = null; 
            Wait('stop');
            $('#form-modal').modal('hide');
            scope.removeAddTreeRefreshed();
            });

        if (scope.removeSaveComplete) {
            scope.removeSaveComplete();
        }
        scope.removeSaveComplete = scope.$on('SaveComplete', function(e, group_id, error) {
            if (!error) {
                if (scope.searchCleanup)
                    scope.searchCleanup();
                scope.formModalActionDisabled = false;
                scope.showGroupHelp = false;  //get rid of the Hint
                BuildTree({ scope: parent_scope, inventory_id: inventory_id, refresh: true, new_group_id: group_id });
            }
            });

        if (scope.removeFormSaveSuccess) {
            scope.removeFormSaveSuccess();
        }
        scope.removeFormSaveSuccess = scope.$on('formSaveSuccess', function(e, group_id, url) {
            
            // Source data gets stored separately from the group. Validate and store Source
            // related fields, then call SaveComplete to wrap things up.

            var parseError = false;
            var saveError = false;
            
            // Update the selector tree with new group name, descr
            //SetNodeName({ scope: scope['selectedNode'], group_id: group_id,
            //    name: scope.name, description: scope.description });

            if (scope.source.value !== null && scope.source.value !== '') {
                var data = {
                    group: group_id, 
                    source: scope['source'].value,
                    source_path: scope['source_path'],
                    credential: scope['credential'],
                    overwrite: scope['overwrite'],
                    overwrite_vars: scope['overwrite_vars'],
                    update_on_launch: scope['update_on_launch']
                    //update_interval: scope['update_interval'].value
                    };

                // Create a string out of selected list of regions
                var regions = $('#s2id_group_source_regions').select2("data");
                var r = [];
                for (var i=0; i < regions.length; i++) {
                    r.push(regions[i].id);
                }
                data['source_regions'] = r.join();
                
                if (scope['source'].value == 'ec2') {
                    // for ec2, validate variable data
                    try {
                         if (scope.envParseType == 'json') {
                            var json_data = JSON.parse(scope.source_vars);  //make sure JSON parses
                         }
                         else {
                            var json_data = jsyaml.load(scope.source_vars);  //parse yaml
                         }
                        
                         // Make sure our JSON is actually an object
                         if (typeof json_data !== 'object') {
                            throw "failed to return an object!";
                         }
                         
                         // Send JSON as a string
                         if ($.isEmptyObject(json_data)) {
                            data.source_vars = "";
                         }
                         else {
                            data.source_vars = JSON.stringify(json_data, undefined, '\t'); 
                         }
                    }
                    catch(err) {
                         parseError = true;
                         scope.$emit('SaveComplete', true);
                         Alert("Error", "Error parsing extra variables. Parser returned: " + err);     
                    }
                }

                if (!parseError) {           
                  Rest.setUrl(url)
                  Rest.put(data)
                      .success( function(data, status, headers, config) {
                          scope.$emit('SaveComplete', group_id, false);
                          })
                      .error( function(data, status, headers, config) {
                          scope.$emit('SaveComplete', group_id, true);
                          ProcessErrors(scope, data, status, form,
                              { hdr: 'Error!', msg: 'Failed to update group inventory source. PUT status: ' + status });
                          });
                }
            }
            else {
               // No source value
               scope.$emit('SaveComplete', group_id, false);
            }
            });
        
        // Cancel
        scope.cancelModal = function() {
            if (scope.searchCleanup) {
                scope.searchCleanup();
            }
            }

        // Save
        scope.formModalAction = function() {
            Wait('start');
            try { 
                scope.formModalActionDisabled = true;

                // Make sure we have valid variable data
                if (scope.parseType == 'json') {
                    var json_data = JSON.parse(scope.variables);  //make sure JSON parses
                }
                else {
                    var json_data = jsyaml.load(scope.variables);  //parse yaml
                }

                // Make sure our JSON is actually an object
                if (typeof json_data !== 'object') {
                    throw "failed to return an object!";
                }

                var data = { 
                    name: scope['name'],
                    description: scope['description']
                    };

                if (inventory_id) {
                    data['inventory'] = inventory_id;
                }

                if ($.isEmptyObject(json_data)) {
                    data['variables'] = "";
                }
                else {
                   data['variables'] = JSON.stringify(json_data, undefined, '\t');
                }

                Rest.setUrl(defaultUrl);
                Rest.post(data)
                    .success( function(data, status, headers, config) {
                        scope.$emit('formSaveSuccess', data.id, GetBasePath('inventory_sources') + data.id + '/');
                        }) 
                    .error( function(data, status, headers, config) {
                        Wait('stop');
                        scope.formModalActionDisabled = false;
                        ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to add new group. POST returned status: ' + status });
                        });
            }
            catch(err) {
                Wait('stop');
                scope.formModalActionDisabled = false;
                Alert("Error", "Error parsing group variables. Parser returned: " + err);     
            }
            }

        scope.sourceChange = function() {
            SourceChange({
                scope: scope, 
                form: GroupForm
                });
            }

        var choicesReady = 0;

        if (scope.removeChoicesReady) {
            scope.removeChoicesReady();  
        }
        scope.removeChoicesReady = scope.$on('choicesReadyGroup', function() {
            choicesReady++; 
            if (choicesReady == 2) {
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

        GetSourceTypeOptions({ scope: scope, variable: 'source_type_options' });
        
        Wait('start');

        }
        }])

    .factory('GroupsEdit', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GroupForm', 'GenerateForm', 
        'Prompt', 'ProcessErrors', 'GetBasePath', 'SetNodeName', 'ParseTypeChange', 'GetSourceTypeOptions', 'InventoryUpdate',
        'GetUpdateIntervalOptions', 'LookUpInit', 'Empty', 'Wait', 'GetChoices', 'UpdateGroup', 'SourceChange', 'Find',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, SetNodeName, ParseTypeChange, GetSourceTypeOptions, InventoryUpdate, GetUpdateIntervalOptions,
        LookUpInit, Empty, Wait, GetChoices, UpdateGroup, SourceChange, Find) {
    return function(params) {
       
        var parent_scope = params.scope;
        var group_id = params.group_id;
        var tree_id = params.tree_id;
        var inventory_id = params.inventory_id;
        var groups_reload = params.groups_reload;
        
        var generator = GenerateForm;
        var form = GroupForm;
        var defaultUrl =  GetBasePath('groups') + group_id + '/';
        var master = {};

        // Load the modal form
        var scope = generator.inject(form, { mode: 'edit', modal: true, related: false, show_modal: false });
        generator.reset();
        
        GetSourceTypeOptions({ scope: scope, variable: 'source_type_options' });
    
        scope.formModalActionLabel = 'Save';
        scope.formModalHeader = 'Group';
        scope.formModalCancelShow = true;
        scope.source = form.fields.source['default'];
        scope.parseType = 'yaml';
        scope[form.fields['source_vars'].parseTypeName] = 'yaml';
        scope.sourcePathRequired = false;
  
        ParseTypeChange(scope);
        ParseTypeChange(scope, 'source_vars', form.fields['source_vars'].parseTypeName);
        
        // After the group record is loaded, retrieve related data
        if (scope.groupLoadedRemove) {
            scope.groupLoadedRemove();
        }
        scope.groupLoadedRemove = scope.$on('groupLoaded', function() {
            if (scope.variable_url) {
                // get group variables
                Rest.setUrl(scope.variable_url);
                Rest.get()
                   .success( function(data, status, headers, config) {
                       if ($.isEmptyObject(data)) {
                           scope.variables = "---";
                       }
                       else {
                           scope.variables = jsyaml.safeDump(data);
                       }
                       Wait('stop');
                       })
                   .error( function(data, status, headers, config) {
                       scope.variables = null;
                       Wait('stop');
                       ProcessErrors(scope, data, status, form,
                           { hdr: 'Error!', msg: 'Failed to retrieve group variables. GET returned status: ' + status });
                       });
            }
            else {
                scope.variables = "---";
            }
            master.variables = scope.variables;

            if (scope.source_url) {
                // get source data
                Rest.setUrl(scope.source_url);
                Rest.get()
                    .success( function(data, status, headers, config) {
                        for (var fld in form.fields) {
                            if (fld == 'checkbox_group') {
                               for (var i = 0; i < form.fields[fld].fields.length; i++) {
                                   var flag = form.fields[fld].fields[i];
                                   if (data[flag.name] !== undefined) {
                                       scope[flag.name] = data[flag.name];
                                       master[flag.name] = scope[flag.name];
                                   }
                               }
                            }
                            if (fld == 'source') {
                                var found = false;
                                for (var i=0; i < scope.source_type_options.length; i++) {
                                    if (scope.source_type_options[i].value == data['source']) {
                                        scope['source'] = scope.source_type_options[i];
                                        found = true;
                                    }  
                                }
                                if (!found || scope['source'].value == "") {
                                    scope['groupUpdateHide'] = true;
                                }
                                else {
                                    scope['groupUpdateHide'] = false;
                                }
                                master['source'] = scope['source'];
                            }
                            else if (fld == 'update_interval') {
                                if (data[fld] == '' || data[fld] == null || data[fld] == undefined) {
                                    data[fld] = 0;
                                }
                                for (var i=0; i < scope.update_interval_options.length; i++) { 
                                    if (scope.update_interval_options[i].value == 
                                        data[fld]) {
                                        scope[fld] = scope.update_interval_options[i];
                                    }
                                }
                            }
                            else if (fld == 'source_vars') {
                                // Parse source_vars, converting to YAML.  
                                if ($.isEmptyObject(data.source_vars) || data.source_vars == "\{\}" || 
                                    data.source_vars == "null" || data.source_vars == "") {
                                    scope.source_vars = "---";
                                }
                                else {
                                    var json_obj = JSON.parse(data.extra_vars);
                                    scope.source_vars = jsyaml.safeDump(json_obj);
                                }
                                master.source_vars = scope.variables;
                            }
                            else if (data[fld]) {
                                scope[fld] = data[fld];
                                master[fld] = scope[fld];
                            }

                            if (form.fields[fld].sourceModel && data.summary_fields &&
                                data.summary_fields[form.fields[fld].sourceModel]) {
                                scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] = 
                                    data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                                master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] = 
                                    data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                            }
                        }
                       
                        scope.sourceChange();   //set defaults that rely on source value
                       
                        if (data['source_regions']) {
                            if (data['source'] == 'ec2' || data['source'] == 'rax') {
                                var set = (data['source'] == 'ec2') ? scope['ec2_regions'] : scope['rax_regions'];
                                var opts = [];
                                var list = data['source_regions'].split(','); 
                                for (var i=0; i < list.length; i++) {
                                    for (var j=0; j < set.length; j++) {
                                        if (list[i] == set[j].value) {
                                           opts.push({ id: set[j].value, text: set[j].label });
                                        }
                                    }
                                }
                                master['source_regions'] = opts;
                                $('#s2id_group_source_regions').select2('data', opts);
                            }
                        }
                        else {
                            // If empty, default to all
                            master['source_regions'] = [{ id: 'all', text: 'All' }];
                        }
                        scope['group_update_url'] = data.related['update'];    
                        Wait('stop');
                        })
                    .error( function(data, status, headers, config) {
                        scope.source = "";
                        Wait('stop');
                        ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to retrieve inventory source. GET status: ' + status });
                        });
            }
            });

        if (scope.removeChoicesComplete) {
            scope.removeChoicesComplete();
        }
        scope.removeChoicesComplete = scope.$on('choicesCompleteGroup', function() {
            // Retrieve detail record and prepopulate the form
            Rest.setUrl(defaultUrl); 
            Rest.get()
                .success( function(data, status, headers, config) {
                    for (var fld in form.fields) {
                        if (data[fld]) {
                            scope[fld] = data[fld];
                            master[fld] = scope[fld];
                        }
                    }
                    scope.variable_url = data.related.variable_data;
                    scope.source_url = data.related.inventory_source;
                    $('#form-modal').modal('show');
                    scope.$emit('groupLoaded');
                    })
                .error( function(data, status, headers, config) {
                    ProcessErrors(scope, data, status, form,
                        { hdr: 'Error!', msg: 'Failed to retrieve group: ' + defaultUrl + '. GET status: ' + status });
                    });
            });
        
        var choicesReady = 0;

        if (scope.removeChoicesReady) {
            scope.removeChoicesReady();  
        }
        scope.removeChoicesReady = scope.$on('choicesReadyGroup', function() {
            choicesReady++; 
            if (choicesReady == 2) {
                scope.$emit('choicesCompleteGroup');
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
        
        Wait('start');

        if (scope.removeSaveComplete) {
            scope.removeSaveComplete();
        }
        scope.removeSaveComplete = scope.$on('SaveComplete', function(e, error) {
            if (!error) {
                // Update the view with any changes
                if (groups_reload) {
                    UpdateGroup({ 
                        scope: parent_scope,
                        group_id: group_id,
                        properties: {
                            name: scope.name,
                            description: scope.description, 
                            has_inventory_sources: (scope.source) ? true : false 
                            }
                        });
                }
                else if (scope.home_groups) {
                    // When home.groups controller is calling, update the groups array
                    var g = Find({ list: parent_scope.home_groups, key: 'id', val: group_id });
                    if (g) {
                        g.name = scope.name;
                        g.description = scope.description;
                    }
                }
               
                //Clean up
                if (scope.searchCleanUp) {
                    scope.searchCleanup();
                }

                scope.formModalActionDisabled = false;
                scope.showGroupHelp = false;  //get rid of the Hint
                
                $('#form-modal').modal('hide');     
                
                // Change the selected group
                if (groups_reload && parent_scope.selected_tree_id !== tree_id) {
                    parent_scope.showHosts(tree_id, group_id, false);
                }
                else {
                    Wait('stop');
                }
            }
            });

        if (scope.removeFormSaveSuccess) {
            scope.removeFormSaveSuccess();
        }
        scope.removeFormSaveSuccess = scope.$on('formSaveSuccess', function(e, group_id) {
            
            // Source data gets stored separately from the group. Validate and store Source
            // related fields, then call SaveComplete to wrap things up.

            var parseError = false;
            var saveError = false;
            
            var data = { group: group_id, 
                source: ( (source && source.value) ? source.value : '' ),
                source_path: scope['source_path'],
                credential: scope['credential'],
                overwrite: scope['overwrite'],
                overwrite_vars: scope['overwrite_vars'],
                update_on_launch: scope['update_on_launch']
                //update_interval: scope['update_interval'].value
                };

            // Create a string out of selected list of regions
            var regions = $('#s2id_group_source_regions').select2("data");
            var r = [];
            for (var i=0; i < regions.length; i++) {
                r.push(regions[i].id);
            }
            data['source_regions'] = r.join();
            
            if (scope['source'].value == 'ec2') {
                // for ec2, validate variable data
                try {
                     if (scope.envParseType == 'json') {
                        var json_data = JSON.parse(scope.source_vars);  //make sure JSON parses
                     }
                     else {
                        var json_data = jsyaml.load(scope.source_vars);  //parse yaml
                     }
                    
                     // Make sure our JSON is actually an object
                     if (typeof json_data !== 'object') {
                        throw "failed to return an object!";
                     }
                     
                     // Send JSON as a string
                     if ($.isEmptyObject(json_data)) {
                        data.source_vars = "";
                     }
                     else {
                        data.source_vars = JSON.stringify(json_data, undefined, '\t'); 
                     }
                }
                catch(err) {
                     parseError = true;
                     scope.$emit('SaveComplete', true);
                     Alert("Error", "Error parsing extra variables. Parser returned: " + err);     
                }
            }

            if (!parseError) {           
              Rest.setUrl(scope.source_url)
              Rest.put(data)
                  .success( function(data, status, headers, config) {
                      scope.$emit('SaveComplete', false);
                      })
                  .error( function(data, status, headers, config) {
                      scope.$emit('SaveComplete', true);
                      ProcessErrors(scope, data, status, form,
                          { hdr: 'Error!', msg: 'Failed to update group inventory source. PUT status: ' + status });
                      });
            }
            });

        // Cancel
        scope.cancelModal = function() {
            if (scope.searchCleanup) {
                scope.searchCleanup();
            }
            }

        // Save
        scope.formModalAction = function() {
            Wait('start');
            try {
                var refreshHosts = false;
       
                // Make sure we have valid variable data
                if (scope.parseType == 'json') {
                   var json_data = JSON.parse(scope.variables);  //make sure JSON parses
                }
                else {
                   var json_data = jsyaml.load(scope.variables);  //parse yaml
                }

                // Make sure our JSON is actually an object
                if (typeof json_data !== 'object') {
                   throw "failed to return an object!";
                }

                var data = {}
                for (var fld in form.fields) {
                    data[fld] = scope[fld];   
                }
                
                data['inventory'] = inventory_id;
                
                Rest.setUrl(defaultUrl);
                Rest.put(data)
                    .success( function(data, status, headers, config) {
                        if (scope.variables) {
                            //update group variables
                            Rest.setUrl(scope.variable_url);
                            Rest.put(json_data)
                                .success( function(data, status, headers, config) {
                                    scope.$emit('formSaveSuccess', data.id);
                                    })
                                .error( function(data, status, headers, config) {
                                    ProcessErrors(scope, data, status, form,
                                        { hdr: 'Error!', msg: 'Failed to update group variables. PUT status: ' + status });
                                    });
                        }
                        else {
                            scope.$emit('formSaveSuccess', data.id);
                        }
                        })
                    .error( function(data, status, headers, config) {
                        Wait('stop');
                        ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to update group: ' + group_id + '. PUT status: ' + status });
                        });
            }
            catch(err) {
               Wait('stop');
               Alert("Error", "Error parsing group variables. Parser returned: " + err);     
            }
            };

        // Start the update process
        scope.updateGroup = function() {
            if (scope.source == "" || scope.source == null) {
              Alert('Missing Configuration', 'The selected group is not configured for updates. You must first edit the group, provide Source settings, ' + 
                  'and then run an update.', 'alert-info');
            }
            else if (scope.status == 'updating') {
              Alert('Update in Progress', 'The inventory update process is currently running for group <em>' +
                  scope.summary_fields.group.name + '</em>. Use the Refresh button to monitor the status.', 'alert-info'); 
            }
            else {
              /*if (scope.source == 'Amazon EC2') {
                 scope.sourceUsernameLabel = 'Access Key ID';
                 scope.sourcePasswordLabel = 'Secret Access Key';
                 scope.sourcePasswordConfirmLabel = 'Confirm Secret Access Key';
              }
              else {
                 scope.sourceUsernameLabel = 'Username';
                 scope.sourcePasswordLabel = 'Password'; 
                 scope.sourcePasswordConfirmLabel = 'Confirm Password';
              }*/
              InventoryUpdate({
                  scope: scope, 
                  group_id: group_id,
                  url: scope.group_update_url,
                  group_name: scope.name, 
                  group_source: scope.source.value
                  });
            }
            }
        
        // Change the lookup and regions when the source changes
        scope.sourceChange = function() {
            SourceChange({
                scope: scope, 
                form: GroupForm
                });
            }

        }
        }])


    .factory('GroupsDelete', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GroupForm', 'GenerateForm', 
        'Prompt', 'ProcessErrors', 'GetBasePath', 'Wait', 'BuildTree', 'Find',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, Wait, BuildTree, Find) {
    return function(params) {
        // Delete the selected group node. Disassociates it from its parent.
        
        var scope = params.scope;
        var tree_id = params.tree_id; 
        var group_id = params.group_id;
        var inventory_id = params.inventory_id;
        
        var node = Find({ list: scope.groups, key: 'id', val: tree_id });
        var url = GetBasePath('inventory') + inventory_id + '/groups/';
        
        var action_to_take = function() {
            $('#prompt-modal').on('hidden.bs.modal', function(){ Wait('start'); });
            $('#prompt-modal').modal('hide');
            Rest.setUrl(url);
            Rest.post({ id: node.group_id, disassociate: 1 })
               .success( function(data, status, headers, config) {
                   $('#prompt-modal').off();
                   scope.$emit('GroupDeleteCompleted'); // Signal a group refresh to start
                   })
               .error( function(data, status, headers, config) {
                   Wait('stop');
                   ProcessErrors(scope, data, status, null,
                       { hdr: 'Error!', msg: 'Call to ' + url + ' failed. POST returned status: ' + status });
                   });      
            };
        
        Prompt({ hdr: 'Delete Group', body: '<p>Are you sure you want to delete group <em>' + node.name + '?</p>',
            action: action_to_take, 'class': 'btn-danger' });
        }
        }])


    .factory('ShowUpdateStatus', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GenerateForm', 
        'Prompt', 'ProcessErrors', 'GetBasePath', 'FormatDate', 'InventoryStatusForm', 'Wait', 'Empty',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, GenerateForm, Prompt, ProcessErrors, GetBasePath,
          FormatDate, InventoryStatusForm, Wait, Empty) {
    return function(params) {

        var group_name = params.group_name;
        var last_update = params.last_update;
        var generator = GenerateForm;
        var form = InventoryStatusForm;
        var license_error = params.license_error;
        var tree_id = params.tree_id;
        var group_id = params.group_id;
        var parent_scope = params.parent_scope;
        
        if (last_update == undefined || last_update == null || last_update == ''){
            Wait('stop');
            Alert('Missing Configuration', 'The selected group is not configured for inventory sync. ' +
                'Edit the group and provide Source information.', 'alert-info');
        }
        else {
            var scope = generator.inject(form, { mode: 'edit', modal: true, related: false, showModal: false });
            generator.reset();
            
            scope.formModalAction = function() {
                $('#form-modal').modal("hide");
                if (parent_scope && parent_scope.showHosts && !Empty(tree_id)) {
                    if (parent_scope.selected_tree_id !== tree_id)
                        parent_scope.showHosts(tree_id, group_id, false);
                }
                }

            if (scope.removeUpdateStatusReady) {
                scope.removeUpdateStatusReady();
            }
            scope.removeUpdateStatusReady = scope.$on('UpdateStatusReady', function(e) {
                scope.formModalActionLabel = 'OK';
                scope.formModalCancelShow = false;
                scope.formModalInfo = false;
                scope.formModalHeader = group_name + '<span class="subtitle"> - Inventory Sync</span>';
                $('#form-modal').modal('show');
                Wait('stop');
                });
            
            // Retrieve detail record and prepopulate the form
            Rest.setUrl(last_update);
            Rest.get()
                .success( function(data, status, headers, config) { 
                    for (var fld in form.fields) {
                        if (data[fld]) {
                           if (fld == 'created') {
                              scope[fld] = FormatDate(new Date(data[fld]));
                           }
                           else {
                              scope[fld] = data[fld];
                           }
                        }
                    }
                    scope.license_error = license_error; 
                    scope.$emit('UpdateStatusReady');
                    })
                .error( function(data, status, headers, config) {
                    $('#form-modal').modal("hide");
                    ProcessErrors(scope, data, status, null,
                        { hdr: 'Error!', msg: 'Failed to retrieve last update: ' + last_update + '. GET status: ' + status });
                    });
        }
        
        }
        }]);








