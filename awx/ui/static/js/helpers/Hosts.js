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
                                'InventoryFormDefinition', 'SelectionHelper'
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

        var defaultUrl = GetBasePath('inventory') + inventory_id + '/hosts/';
        var view = GenerateList;

        var scope = view.inject(list, {
            id: 'form-modal-body', 
            mode: 'select',
            breadCrumbs: false,
            selectButton: false
            });
        
        scope.formModalActionLabel = 'Select';
        scope.formModalHeader = 'Select Hosts';
        scope.formModalCancelShow = true;
    
        SelectionInit({ scope: scope, list: list, url: GetBasePath('groups') + group_id + '/hosts/' });

        if (scope.removeModalClosed) {
           scope.removeModalClosed();
        }
        scope.removeModalClosed = scope.$on('modalClosed', function() {
            // if the modal cloased, assume something got changed and reload the host list
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
        scope.formModalHeader = 'Create Host';
        scope.formModalCancelShow = true;
        scope.parseType = 'yaml';
        ParseTypeChange(scope);
        
        if (scope.removeHostsReload) {
           scope.removeHostsReload();
        }
        scope.removeHostsReload = scope.$on('hostsReload', function() {
            console.log('here!');
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
               
               Rest.setUrl(defaultUrl);
               Rest.post(data)
                   .success( function(data, status, headers, config) {
                       if (scope.variables) {
                          Rest.setUrl(data.related.variable_data);
                          Rest.put(json_data)
                              .success( function(data, status, headers, config) {
                                  finished();
                              })
                              .error( function(data, status, headers, config) {
                                  ProcessErrors(scope, data, status, form,
                                     { hdr: 'Error!', msg: 'Failed to add host varaibles. PUT returned status: ' + status });
                              });
                       }
                       else {
                          finished();
                       }
                       })
                   .error( function(data, status, headers, config) {
                       ProcessErrors(scope, data, status, form,
                           { hdr: 'Error!', msg: 'Failed to add new host. POST returned status: ' + status });
                       });
           }
           catch(err) {
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
        scope.formModalHeader = 'Edit Host';
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
                Rest.setUrl(defaultUrl);
                Rest.put(data)
                    .success( function(data, status, headers, config) {
                        if (scope.variables) {
                           //update host variables
                           Rest.setUrl(GetBasePath('hosts') + data.id + '/variable_data/');
                           Rest.put(json_data)
                               .success( function(data, status, headers, config) {
                                   finished();
                               })
                               .error( function(data, status, headers, config) {
                                   ProcessErrors(scope, data, status, form,
                                       { hdr: 'Error!', msg: 'Failed to update host varaibles. PUT returned status: ' + status });
                                   });
                        }
                        else {
                           finished();
                        }
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
            var errors = false;
            var maxI;
            
            // Find index pointing to the last selected host
            for (var i=0; i < scope.hosts.length; i++) {
                if (scope.hosts[i].selected) {
                   maxI = i;
                }
            }
            
            function emit(i) {
               // After we process the last selected host or after we hit a problem, refresh the host list
               if (i >= maxI || errors) {
                  $('#prompt-modal').modal('hide');
                  scope.$emit('hostsReload'); 
               }
            }
            
            Rest.setUrl(url);
            for (var i=0; i < scope.hosts.length && !errors; i++) {
                if (scope.hosts[i].selected) {
                   Rest.post({ id: scope.hosts[i].id, disassociate: 1 })
                       .success( function(data, status, headers, config) {
                           // if this is the last selected host, clean up and exit
                           emit(i);
                           })
                       .error( function(data, status, headers, config) {
                           errors = true;
                           emit(i);
                           ProcessErrors(scope, data, status, null,
                               { hdr: 'Error!', msg: 'Attempt to delete ' + scope.hosts[i].name + ' failed. POST returned status: ' + status });
                           });    
                }
            }
            }

        //Force binds to work (not working usual way), and launch the confirmation prompt
        if (scope.group_id == null || req == 'delete') {
           scope['promptHeader'] = 'Delete Host';
           scope['promptBody'] = 'Are you sure you want to permanently delete the selected hosts?';
           scope['promptActionBtnClass'] = 'btn-danger';
        }
        
        /*else {
           scope['promptHeader'] = 'Remove Host from Group';
           scope['promptBody'] = 'Are you sure you want to remove ' + host_name + ' from the group? ' + 
               host_name + ' will continue to be part of the inventory under All Hosts.';
           scope['promptActionBtnClass'] = 'btn-success';  
        }*/
        
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


    .factory('HostsReload', ['RelatedSearchInit', 'RelatedPaginateInit', 'InventoryForm', 'GetBasePath',
    function(RelatedSearchInit, RelatedPaginateInit, InventoryForm, GetBasePath) {
    return function(params) {
        // Rerfresh the Hosts view on right side of page
        
        var group_id = params.group_id;
        var scope = params.scope;
        scope['hosts'] = null;
        scope['toggleAllFlag'] = false;
        scope['hostDeleteHide'] = true;
        
        var url = (group_id !== null && group_id !== undefined) ? GetBasePath('groups') + group_id + '/all_hosts/' :
                  GetBasePath('inventory') + params.inventory_id + '/hosts/';

        var relatedSets = { hosts: { url: url, iterator: 'host' } };
        RelatedSearchInit({ scope: params.scope, form: InventoryForm, relatedSets: relatedSets });
        RelatedPaginateInit({ scope: params.scope, relatedSets: relatedSets, pageSize: 40 });
        
        if (scope['hostFailureFilter']) {
           // If the user checked 'show only hosts with failures', filter for hosts with failed jobs
           scope['hostSearchFieldLabel'] = 'Failed jobs?';
           scope['hostSearchField'] = 'has_active_failures';
           scope['hostSelectShow'] = true;
           scope.setSearchField('host','has_active_failures','Failed jobs?');
           for (var i=0; i < scope['hostSearchSelectOpts'].length; i++) {
               if (scope['hostSearchSelectOpts'][i].value == 1) {
                  scope['hostSearchSelectValue'] = scope['hostSearchSelectOpts'][i];
               }
           }
        }
        
        scope.search('host');
        
        if (!params.scope.$$phase) {
           params.scope.$digest();
        }
        }
        }])

    .factory('LoadSearchTree', ['Rest', 'GetBasePath', 'ProcessErrors', '$compile', 
    function(Rest, GetBasePath, ProcessErrors, $compile) {
    return function(params) {
         
        var scope = params.scope; 
        var inventory_id = params.inventory_id;
        var newTree = [];
        scope.searchTree = [];
            
        // Load the root node
        Rest.setUrl (GetBasePath('inventory') + inventory_id + '/');
        Rest.get()
             .success( function(data, status, headers, config) {
                 scope.searchTree.push({
                     name: data.name, 
                     description: data.description, 
                     hosts: data.related.hosts,
                     failures: data.has_active_failures,
                     groups: data.related.root_groups,
                     children: []
                     });
                 scope.$emit('hostTabInit');
                 })
             .error( function(data, status, headers, config) {
                 ProcessErrors(scope, data, status, null,
                     { hdr: 'Error!', msg: 'Failed to get inventory: ' + inventory_id + '. GET returned: ' + status });
                 });
        }
        }]);
     




