/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  HostsHelper
 *
 *  Routines that handle host add/edit/delete on the Inventory detail page.
 *  
 */

angular.module('HostsHelper', [ 'RestServices', 'Utilities', 'ListGenerator', 'HostListDefinition',
                                'SearchHelper', 'PaginateHelper', 'ListGenerator', 'AuthService', 'HostsHelper',
                                'InventoryHelper', 'RelatedSearchHelper','RelatedPaginateHelper', 
                                'InventoryFormDefinition', 'SelectionHelper', 'HostGroupsFormDefinition', 
                                'InventoryHostsFormDefinition'
                                ])

    .factory('HostsList', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'HostList', 'GenerateList', 
        'Prompt', 'SearchInit', 'PaginateInit', 'ProcessErrors', 'GetBasePath', 'HostsAdd', 'HostsReload',
        'SelectionInit',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, HostList, GenerateList, Prompt, SearchInit,
        PaginateInit, ProcessErrors, GetBasePath, HostsAdd, HostsReload, SelectionInit) {
    return function(params) {
        
        var inventory_id = params.inventory_id;
        var group_id = params.group_id;
        
        var list = HostList;

        list.iterator = 'subhost';  //Override the iterator and name so the scope of the modal dialog
        list.name = 'subhosts';     //will not conflict with the parent scope

        var view = GenerateList;

        var scope = view.inject(list, {
            id: 'form-modal-body', 
            mode: 'select',
            breadCrumbs: false,
            selectButton: false
            });
        
        var defaultUrl = GetBasePath('inventory') + inventory_id + '/hosts/?not__groups__id=' + scope.group_id;
        
        scope.formModalActionLabel = 'Select';
        scope.formModalHeader = 'Add Existing Hosts';
        scope.formModalCancelShow = true;
    
        SelectionInit({ scope: scope, list: list, url: GetBasePath('groups') + group_id + '/hosts/' });

        if (scope.removeModalClosed) {
           scope.removeModalClosed();
        }
        scope.removeModalClosed = scope.$on('modalClosed', function() {
            // if the modal closed, assume something got changed and reload the host list
            HostsReload(params);
        });
        
        $('.popover').popover('hide');  //remove any lingering pop-overs
        $('#form-modal .btn-none').removeClass('btn-none').addClass('btn-success');
        $('#form-modal').modal({ backdrop: 'static', keyboard: false });
        
        SearchInit({ scope: scope, set: 'subhosts', list: list, url: defaultUrl });
        PaginateInit({ scope: scope, list: list, url: defaultUrl, mode: 'lookup' });
        scope.search(list.iterator);

        if (!scope.$$phase) {
           scope.$digest();
        }

        scope.createHost = function() {
            $('#form-modal').modal('hide');
            HostsAdd({ scope: params.scope, inventory_id: inventory_id, group_id: group_id });
            }

        }
        }])


    .factory('HostsAdd', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'HostForm', 'GenerateForm', 
        'Prompt', 'ProcessErrors', 'GetBasePath', 'HostsReload', 'ParseTypeChange',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, HostForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, HostsReload, ParseTypeChange) {
    return function(params) {

        var inventory_id = params.inventory_id;
        var group_id = (params.group_id !== undefined) ? params.group_id : null;

        // Inject dynamic view
        var defaultUrl = GetBasePath('groups') + group_id + '/hosts/';
        var form = HostForm;
        var generator = GenerateForm;
        var scope = generator.inject(form, {mode: 'add', modal: true, related: false});
        
        scope.formModalActionLabel = 'Save';
        scope.formModalHeader = 'Create New Host';
        scope.formModalCancelShow = true;
        scope.parseType = 'yaml';
        ParseTypeChange(scope);
        
        if (scope.removeHostsReload) {
           scope.removeHostsReload();
        }
        scope.removeHostsReload = scope.$on('hostsReload', function() {
            HostsReload(params);
        });

        $('#form-modal .btn-none').removeClass('btn-none').addClass('btn-success');
        //$('#form-modal').unbind('hidden');
        //$('#form-modal').on('hidden', function () { scope.$emit('hostsReload'); });
        
        generator.reset();
        var master={};

        if (!scope.$$phase) {
           scope.$digest();
        }

        // Save
        scope.formModalAction  = function() {
           
           function finished() {
               $('#form-modal').modal('hide');
               scope.$emit('hostsReload'); 
               }

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

               var data = {}
               for (var fld in form.fields) {
                   if (fld != 'variables') {
                      data[fld] = scope[fld];   
                   }
               }
               
               data['inventory'] = inventory_id;
               
               if ($.isEmptyObject(json_data)) {
                  data['variables'] = "";
               }
               else {
                  data['variables'] = JSON.stringify(json_data, undefined, '\t');
               }

               Rest.setUrl(defaultUrl);
               Rest.post(data)
                   .success( function(data, status, headers, config) {
                       finished();
                       })
                   .error( function(data, status, headers, config) {
                       scope.formModalActionDisabled = false;
                       ProcessErrors(scope, data, status, form,
                           { hdr: 'Error!', msg: 'Failed to add new host. POST returned status: ' + status });
                       });
           }
           catch(err) {
               scope.formModalActionDisabled = false;
               Alert("Error", "Error parsing host variables. Parser returned: " + err);  
           }
           }

        // Cancel
        scope.formReset = function() {
           // Defaults
           generator.reset();
           }; 

        }
        }])


    .factory('HostsEdit', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'HostForm', 'GenerateForm', 
        'Prompt', 'ProcessErrors', 'GetBasePath', 'HostsReload', 'ParseTypeChange',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, HostForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, HostsReload, ParseTypeChange) {
    return function(params) {
        
        var host_id = params.host_id;
        var inventory_id = params.inventory_id;
        var group_id = params.group_id;
        
        var generator = GenerateForm;
        var form = HostForm;
        var defaultUrl =  GetBasePath('hosts') + host_id + '/';
        var scope = generator.inject(form, { mode: 'edit', modal: true, related: false});
        generator.reset();
        var master = {};
        var relatedSets = {};

        scope.formModalActionLabel = 'Save';
        scope.formModalHeader = 'Host Properties';
        scope.formModalCancelShow = true;
        scope.parseType = 'yaml';
        ParseTypeChange(scope);

        if (scope.removeHostsReload) {
           scope.removeHostsReload();
        }
        scope.removeHostsReload = scope.$on('hostsReload', function() {
            HostsReload(params);
        });
        
        $('#form-modal .btn-none').removeClass('btn-none').addClass('btn-success');
        //$('#form-modal').unbind('hidden');
        //$('#form-modal').on('hidden', function () { scope.$emit('hostsReload'); });

        // After the group record is loaded, retrieve any group variables
        if (scope.hostLoadedRemove) {
           scope.hostLoadedRemove();
        }
        scope.hostLoadedRemove = scope.$on('hostLoaded', function() {
            if (scope.variable_url) {
               Rest.setUrl(scope.variable_url);
               Rest.get()
                   .success( function(data, status, headers, config) {
                       if ($.isEmptyObject(data)) {
                          scope.variables = "---";
                       }
                       else {
                          scope.variables = jsyaml.safeDump(data);
                       }
                       })
                   .error( function(data, status, headers, config) {
                       scope.variables = null;
                       ProcessErrors(scope, data, status, form,
                           { hdr: 'Error!', msg: 'Failed to retrieve host variables. GET returned status: ' + status });
                       });
            }
            else {
               scope.variables = "---";
            }
            master.variables = scope.variables;
            });

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
                var related = data.related;
                for (var set in form.related) {
                    if (related[set]) {
                       relatedSets[set] = { url: related[set], iterator: form.related[set].iterator };
                    }
                }
                scope.variable_url = data.related.variable_data;
                scope.$emit('hostLoaded');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, form,
                    { hdr: 'Error!', msg: 'Failed to retrieve host: ' + id + '. GET returned status: ' + status });
                });
       
        if (!scope.$$phase) {
           scope.$digest();
        }
        
        // Save changes to the parent
        scope.formModalAction = function() {
            
            function finished() {
                $('#form-modal').modal('hide');
                scope.$emit('hostsReload');
                }

            try { 
                
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

                if ($.isEmptyObject(json_data)) {
                   data['variables'] = "";
                }
                else {
                   data['variables'] = JSON.stringify(json_data, undefined, '\t');
                }

                Rest.setUrl(defaultUrl);
                Rest.put(data)
                    .success( function(data, status, headers, config) {
                        finished();
                        })
                    .error( function(data, status, headers, config) {
                        ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to update host: ' + host_id + '. PUT returned status: ' + status });
                        });
            }
            catch(err) {
               Alert("Error", "Error parsing host variables. Parser returned: " + err);     
            }
            };

        // Cancel
        scope.formReset = function() {
           generator.reset();
           for (var fld in master) {
               scope[fld] = master[fld];
           }
           scope.parseType = 'yaml';
           }
        }
        }])


    .factory('HostsDelete', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'Prompt', 'ProcessErrors', 'GetBasePath',
        'HostsReload',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, Prompt, ProcessErrors, GetBasePath, HostsReload) {
    return function(params) {
        // Remove the selected host from the current group by disassociating
       
        var scope = params.scope;
        var group_id = scope.group_id; 
        var inventory_id = params.inventory_id;
        var host_id = params.host_id;
        var host_name = params.host_name;
        var req = (params.request) ? params.request : null;

        var url = (scope.group_id == null || req == 'delete') ? GetBasePath('inventory') + inventory_id + '/hosts/' : 
            GetBasePath('groups') + scope.group_id + '/hosts/';
        
        if (scope.removeHostsReload) {
           scope.removeHostsReload();
        }
        scope.removeHostsReload = scope.$on('hostsReload', function() {
            HostsReload(params);
            });

        var action_to_take = function() {
            Rest.setUrl(url);
            Rest.post({ id: host_id, disassociate: 1 })
                .success( function(data, status, headers, config) {
                    $('#prompt-modal').modal('hide');
                    scope.$emit('hostsReload'); 
                    })
                .error( function(data, status, headers, config) {
                    $('#prompt-modal').modal('hide');
                    scope.$emit('hostsReload'); 
                    ProcessErrors(scope, data, status, null,
                        { hdr: 'Error!', msg: 'Attempt to delete ' + host_name + ' failed. POST returned status: ' + status });
                    });    
            }

        //Force binds to work (not working usual way), and launch the confirmation prompt
        if (scope.group_id == null || req == 'delete') {
           scope['promptHeader'] = 'Delete Host';
           scope['promptBody'] = 'Are you sure you want to permanently delete the selected hosts?';
           scope['promptActionBtnClass'] = 'btn-danger';
        }
        
        scope.promptAction = action_to_take;

        $('#prompt-modal').modal({
            backdrop: 'static',
            keyboard: true,
            show: true
            });

        if (!scope.$$phase) {
           scope.$digest();
        }

        }
        }])


    .factory('HostsReload', ['$location', '$routeParams', 'SearchInit', 'PaginateInit', 'InventoryHostsForm', 'GetBasePath', 'Wait',
    function($location, $routeParams, SearchInit, PaginateInit, InventoryHostsForm, GetBasePath, Wait) {
    return function(params) {
        // Rerfresh the Hosts view on right side of page
        
        var scope = params.scope;
        var group_id = scope.group_id;
        var postAction = params.action;
        
        scope['hosts'] = null;
        scope['toggleAllFlag'] = false;
        scope['hostDeleteHide'] = true;
        
        var url = (group_id !== null && group_id !== undefined) ? GetBasePath('groups') + group_id + '/all_hosts/' :
                  GetBasePath('inventory') + params.inventory_id + '/hosts/';

        // Set the groups value in each element of hosts array
        if (scope.removePostRefresh) {
           scope.removePostRefresh();
        }
        scope.removePostRefresh = scope.$on('PostRefresh', function() {

            // Add a list of groups to each host
            var groups, descr, found, list;
            for (var i=0; i < scope.hosts.length; i++) {
                groups = scope.hosts[i].summary_fields.groups;
                scope.hosts[i].groups = '';
                for (var k=0; k < groups.length; k++) {
                    if (!groups[k].name.match(/^_deleted/)) {
                       scope.hosts[i].groups += groups[k].name + ', '
                    }
                }
                scope.hosts[i].groups = scope.hosts[i].groups.replace(/\, $/,'');
               
                if (scope.hosts[i].has_inventory_sources) {
                   scope.hosts[i].inventory_sources = 'yes';
                   scope.hosts[i].has_inv_source_link = '/#/inventories/' + scope['inventory_id'] + '/groups/?has_external_source=true';
                   scope.hosts[i].has_inv_source_tip = 'Has an external source. Click to view inventory source details.';
                }
                else {
                   scope.hosts[i].inventory_sources = 'no';
                   scope.hosts[i].has_inv_source_link = '/#/inventories/' + scope['inventory_id'] + '/groups';
                   scope.hosts[i].has_inv_source_tip = 'Has no external source.';
                }

            }
           
            // Add the value displayed in Job Status column
            for (var i=0; i < scope.hosts.length; i++) {
                scope.hosts[i].activeFailuresLink = '/#/hosts/' + scope.hosts[i].id + '/job_host_summaries/?inventory=' + scope['inventory_id'] +
                    '&host_name=' + escape(scope.hosts[i].name); 
                if (scope.hosts[i].has_active_failures == true) {
                   scope.hosts[i].badgeToolTip = 'Most recent job failed. Click to view jobs.';
                   scope.hosts[i].active_failures = 'failed';
                }
                else if (scope.hosts[i].has_active_failures == false && scope.hosts[i].last_job == null) {
                   scope.hosts[i].has_active_failures = 'none';
                   scope.hosts[i].badgeToolTip = "No job data available.";
                   scope.hosts[i].active_failures = 'n/a';
                }
                else if (scope.hosts[i].has_active_failures == false && scope.hosts[i].last_job !== null) {
                   scope.hosts[i].badgeToolTip = "Most recent job successful. Click to view jobs.";
                   scope.hosts[i].active_failures = 'success';
                }        
            }

            if (group_id == null || group_id == undefined) {
               if (!scope.hosts.length) {
                  scope.$emit('ShowHelp');
               }
            }
         
            if (postAction) {
               postAction();
            }

            });
        
        SearchInit({ scope: scope, set: 'hosts', list: InventoryHostsForm, url: url });
        PaginateInit({ scope: scope, list: InventoryHostsForm, url: url });
        
        if ($routeParams['has_active_failures']) {
           //scope.resetSearch(InventoryHostsForm.iterator);
           scope[InventoryHostsForm.iterator + 'InputDisable'] = true;
           scope[InventoryHostsForm.iterator + 'SearchValue'] = $routeParams['has_active_failures'];
           scope[InventoryHostsForm.iterator + 'SearchField'] = 'has_active_failures';
           scope[InventoryHostsForm.iterator + 'SearchFieldLabel'] = InventoryHostsForm.fields['has_active_failures'].label;
           scope[InventoryHostsForm.iterator + 'SearchSelectValue'] = ($routeParams['has_active_failures'] == 'true') ? { value: 1 } : { value: 0 };
           
        }
        else if ($routeParams['name']) {
           scope[InventoryHostsForm.iterator + 'InputDisable'] = false;
           scope[InventoryHostsForm.iterator + 'SearchValue'] = $routeParams['name'];
           scope[InventoryHostsForm.iterator + 'SearchField'] = 'name';
           scope[InventoryHostsForm.iterator + 'SearchFieldLabel'] = InventoryHostsForm.fields['name'].label;
           scope[InventoryHostsForm.iterator + 'SearchSelectValue'] = null;
        }

        scope.search(InventoryHostsForm.iterator);
        
        if (!params.scope.$$phase) {
           params.scope.$digest();
        }
        }
        }])

    .factory('EditHostGroups', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GenerateForm', 
        'Prompt', 'ProcessErrors', 'GetBasePath', 'HostsReload', 'ParseTypeChange', 'Wait',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, HostsReload, ParseTypeChange, Wait) {
    return function(params) {
        
        var host_id = params.host_id;
        var inventory_id = params.inventory_id;
        var generator = GenerateForm;
        var actions = [];
        
        //var html="<div class=\"host-groups-title\"><h4>{{ host.name }}</h4></div>\n";
        var html = "<div class=\"row host-groups\">\n";
        html += "<div class=\"col-lg-6\">\n";
        html += "<label>Available Groups:</label>\n";
        html += "<select multiple class=\"form-control\" name=\"available-groups\" ng-model=\"selectedGroups\" ng-change=\"leftChange()\" " +
            "ng-options=\"avail_group.name for avail_group in available_groups\"></select>\n";
        html += "</div>\n";
        html += "<div class=\"col-lg-6\">\n";
        html += "<label>Belongs to Groups:</label>\n";
        html += "<select multiple class=\"form-control\" name=\"selected-groups\" ng-model=\"assignedGroups\" ng-change=\"rightChange()\" " +
            "ng-options=\"host_group.name for host_group in host_groups\"></select>\n";
        html += "</div>\n";
        html += "</div>\n";
        html += "<div class=\"row host-group-buttons\">\n";
        html += "<div class=\"col-lg-12\">\n";
        html += "<button type=\"button\" ng-click=\"moveLeft()\" class=\"btn btn-sm btn-primary left-button\" ng-disabled=\"leftButtonDisabled\">" +
            "<i class=\"icon-arrow-left\"></i></button>\n";
        html += "<button type=\"button\" ng-click=\"moveRight()\" class=\"btn btn-sm btn-primary right-button\" ng-disabled=\"rightButtonDisabled\">" +
            "<i class=\"icon-arrow-right\"></i></button>\n";
        html += "<p>(move selected groups)</p>\n";
        html += "</div>\n";
        html += "</div>\n";

        var defaultUrl =  GetBasePath('hosts') + host_id + '/';
        var scope = generator.inject(null, { mode: 'edit', modal: true, related: false, html: html });
        
        for (var i=0; i < scope.hosts.length; i++) {
           if (scope.hosts[i].id == host_id) {
               scope.host = scope.hosts[i];
           }  
        }

        scope.selectedGroups = null;
        scope.assignedGroups = null;
        scope.leftButtonDisabled = true;
        scope.rightButtonDisabled = true; 

        scope.formModalActionLabel = 'Save';
        //scope.formModalHeader = 'Host Groups';
        scope.formModalHeader = scope.host.name + ' - <span class=\"subtitle\">Groups</span>';
        scope.formModalCancelShow = true;
        scope.formModalActionDisabled = true;

        $('#form-modal .btn-none').removeClass('btn-none').addClass('btn-success');

        if (scope.hostGroupChangeRemove) {
           scope.hostGroupChangeRemove();
        }
        scope.hostGroupChangeRemove = scope.$on('hostGroupChange', function(e) {
            actions.pop();
            if (actions.length == 0) {
               var postAction = function() { 
                   setTimeout(function() { Wait('stop') }, 500); 
                   };
               HostsReload({ scope: scope, inventory_id: inventory_id, group_id: scope.group_id , action: postAction });
            }
            }); 
        
        // Save changes
        scope.formModalAction = function() {
            var found;
          
            $('#form-modal').modal('hide');
            Wait('start');

            // removed host from deleted groups
            for (var i=0; i < scope.original_groups.length; i++) {
                found = false;
                for (var j=0; j < scope.host_groups.length; j++) {
                    if (scope.original_groups[i].id == scope.host_groups[j].id) {
                       found = true;
                    }
                }
                if (!found) {
                   // group was removed 
                   actions.push({ group_id: scope.original_groups[i].id , action: 'delete' });
                   Rest.setUrl(GetBasePath('groups') + scope.original_groups[i].id + '/hosts/');
                   Rest.post({ id: host_id, disassociate: 1 })
                       .success( function(data, status, headers, config) {
                           scope.$emit('hostGroupChange');
                           })
                       .error( function(data, status, headers, config) {
                           scope.$emit('hostGroupChange');
                           ProcessErrors(scope, data, status, null,
                               { hdr: 'Error!', msg: 'Attempt to remove host from group ' + scope.original_groups[i].name +
                               ' failed. POST returned status: ' + status });
                           });
                }
            }

            // add host to new groups
            for (var i=0; i < scope.host_groups.length; i++) {
                found = false; 
                for (var j=0; j < scope.original_groups.length; j++) {
                    if (scope.original_groups[j].id == scope.host_groups[i].id) {
                       found = true;
                    } 
                } 
                if (!found) {
                   // group was added
                   actions.push({ group_id: scope.host_groups[i].id , action: 'add' });
                   Rest.setUrl(GetBasePath('groups') + scope.host_groups[i].id + '/hosts/');
                   Rest.post(scope.host)
                       .success( function(data, status, headers, config) {
                           scope.$emit('hostGroupChange');
                           })
                       .error( function(data, status, headers, config) {
                           scope.$emit('hostGroupChange');
                           ProcessErrors(scope, data, status, null,
                               { hdr: 'Error!', msg: 'Attempt to add host to group ' + scope.host_groups[i].name +
                               ' failed. POST returned status: ' + status });
                           });
                }
            }
            }

        scope.leftChange = function() {
            // Select/deselect on available groups list
            if (scope.selectedGroups !== null && scope.selectedGroups.length > 0) {
               scope.assignedGroups = null;
               scope.leftButtonDisabled = true;
               scope.rightButtonDisabled = false;
            }
            else {
               scope.rightButtonDisabled = true;
            }
            }
 
        scope.rightChange = function() {
            // Select/deselect made on host groups list
            if (scope.assignedGroups !== null && scope.assignedGroups.length > 0) {
               scope.selectedGroups = null;
               scope.leftButtonDisabled = false;
               scope.rightButtonDisabled = true;
            }
            else {
               scope.leftButtonDisabled = true;
            }
            }

        scope.moveLeft = function() {
            // Remove selected groups from the list of assigned groups
            for (var i=0; i < scope.assignedGroups.length; i++){
               for (var j=0 ; j < scope.host_groups.length; j++) {
                   if (scope.host_groups[j].id == scope.assignedGroups[i].id) {
                      scope.host_groups.splice(j,1);
                      break;
                   }
               }  
            }
            var found, placed;
            for (var i=0; i < scope.assignedGroups.length; i++){
               found = false;
               for (var j=0; j < scope.available_groups.length && !found; j++){
                   if (scope.available_groups[j].id == scope.assignedGroups[i].id) {
                      found=true;
                   }
               }
               if (!found) {
                  placed = false; 
                  for (var j=0; j < scope.available_groups.length && !placed; j++){
                      if (j == 0 && scope.assignedGroups[i].name.toLowerCase() < scope.available_groups[j].name.toLowerCase()) {
                         // prepend to the beginning of the array
                         placed=true;
                         scope.available_groups.unshift(scope.assignedGroups[i]);
                      }
                      else if (j + 1 < scope.available_groups.length) {
                         if (scope.assignedGroups[i].name.toLowerCase() > scope.available_groups[j].name.toLowerCase() && 
                             scope.assignedGroups[i].name.toLowerCase() < scope.available_groups[j + 1].name.toLowerCase() ) {
                             // insert into the middle of the array
                             placed = true;
                             scope.available_groups.splice(j + 1, 0, scope.assignedGroups[i]);
                         }
                      }
                  }
                  if (!placed) {
                     // append to the end of the array
                     scope.available_groups.push(scope.assignedGroups[i]);
                  }
               }
            }
            scope.assignedGroups = null;
            scope.leftButtonDisabled = true; 
            scope.rightButtonDisabled = true;
            scope.formModalActionDisabled = false;
            }

        scope.moveRight = function() {
             // Remove selected groups from list of available groups
            for (var i=0; i < scope.selectedGroups.length; i++){
               for (var j=0 ; j < scope.available_groups.length; j++) {
                   if (scope.available_groups[j].id == scope.selectedGroups[i].id) {
                      scope.available_groups.splice(j,1);
                      break; 
                   }
               }
            }
            var found, placed;
            for (var i=0; i < scope.selectedGroups.length; i++){
               found = false;
               for (var j=0; j < scope.host_groups.length && !found; j++){
                   if (scope.host_groups[j].id == scope.selectedGroups[i].id) {
                      found=true;
                   }
               }
               if (!found) {
                  placed = false; 
                  for (var j=0; j < scope.host_groups.length && !placed; j++){
                      if (j == 0 && scope.selectedGroups[i].name.toLowerCase() < scope.host_groups[j].name.toLowerCase()) {
                         // prepend to the beginning of the array
                         placed=true;
                         scope.host_groups.unshift(scope.selectedGroups[i]);
                      }
                      else if (j + 1 < scope.host_groups.length) {
                         if (scope.selectedGroups[i].name.toLowerCase() > scope.host_groups[j].name.toLowerCase() && 
                             scope.selectedGroups[i].name.toLowerCase() < scope.host_groups[j + 1].name.toLowerCase() ) {
                             // insert into the middle of the array
                             placed = true;
                             scope.host_groups.splice(j + 1, 0, scope.selectedGroups[i]);
                         }
                      }
                  }
                  if (!placed) {
                     // append to the end of the array
                     scope.host_groups.push(scope.selectedGroups[i]);
                  }
               }
            }
            scope.selectedGroups = null;
            scope.leftButtonDisabled = true; 
            scope.rightButtonDisabled = true;
            scope.formModalActionDisabled = false;
            }


        // Load the host's current list of groups
        scope.host_groups = [];
        scope.original_groups = [];
        scope.available_groups = [];
        Rest.setUrl(scope.host.related.groups + '?order_by=name');
        Rest.get()
            .success( function(data, status, headers, config) {
                for (var i=0; i < data.results.length; i++) {
                    scope.host_groups.push({ 
                        id: data.results[i].id, 
                        name: data.results[i].name,
                        description: data.results[i].description
                        });
                    scope.original_groups.push({ 
                        id: data.results[i].id, 
                        name: data.results[i].name,
                        description: data.results[i].description
                        });
                }
                var found; 
                for (var i=0; i < scope.inventory_groups.length; i++) {
                    found =  false;
                    for (var j=0; j < scope.host_groups.length; j++) {
                        if (scope.inventory_groups[i].id == scope.host_groups[j].id) {
                           found = true; 
                        }  
                    }
                    if (!found) {
                       scope.available_groups.push(scope.inventory_groups[i]);
                    }
                }
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                     { hdr: 'Error!', msg: 'Failed to get current groups for host: ' + host_id + '. GET returned: ' + status });
                });

        if (scope.removeHostsReload) {
           scope.removeHostsReload();
        }
        scope.removeHostsReload = scope.$on('hostsReload', function() {
            HostsReload(params);
        });
        
        
        // After the group record is loaded, retrieve any group variables
        if (scope.hostLoadedRemove) {
           scope.hostLoadedRemove();
        }
        scope.hostLoadedRemove = scope.$on('hostLoaded', function() {
            
            });

       
        if (!scope.$$phase) {
           scope.$digest();
        }
        
           
        }
        }]);

     




