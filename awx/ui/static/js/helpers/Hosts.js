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
                                'InventoryFormDefinition'
                                ])

    .factory('HostsList', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'HostList', 'GenerateList', 
        'Prompt', 'SearchInit', 'PaginateInit', 'ProcessErrors', 'GetBasePath', 'HostsAdd', 'HostsReload',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, HostList, GenerateList, LoadBreadCrumbs, SearchInit,
        PaginateInit, ProcessErrors, GetBasePath, HostsAdd, HostsReload) {
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

        if (scope.removeHostsReload) {
           scope.removeHostsReload();
        }
        scope.removeHostsReload = scope.$on('hostsReload', function() {
            HostsReload(params);
        });

        $('#form-modal .btn-none').removeClass('btn-none').addClass('btn-success');
        $('#form-modal').modal({ backdrop: 'static', keyboard: false });
        
        scope.selected = [];
        
        if (scope.PostRefreshRemove) {
           scope.PostRefreshRemove();
        }
        scope.PostRefreshRemove = scope.$on('PostRefresh', function() {
            $("tr.success").each(function(index) {
                // Make sure no rows have a green background 
                var ngc = $(this).attr('ng-class'); 
                scope[ngc] = ""; 
                });
            });

        SearchInit({ scope: scope, set: 'subhosts', list: list, url: defaultUrl });
        PaginateInit({ scope: scope, list: list, url: defaultUrl, mode: 'lookup' });
        scope.search(list.iterator);

        if (!scope.$$phase) {
           scope.$digest();
        }

        scope.formModalAction = function() {
           var url = GetBasePath('groups') + group_id + '/hosts/'; 
           Rest.setUrl(url);
           scope.queue = [];

           if (scope.callFinishedRemove) {
              scope.callFinishedRemove();
           }
           scope.callFinishedRemove = scope.$on('callFinished', function() {
              // We call the API for each selected item. We need to hang out until all the api
              // calls are finished.
              if (scope.queue.length == scope.selected.length) {
                 // All the api calls finished
                 $('input[type="checkbox"]').prop("checked",false);
                 scope.selected = [];
                 var errors = 0;   
                 for (var i=0; i < scope.queue.length; i++) {
                     if (scope.queue[i].result == 'error') {
                        errors++;
                     }
                 }
                 if (errors > 0) {
                    Alert('Error', 'There was an error while adding one or more of the selected hosts.');  
                 }
                 $('#form-modal').modal('hide');
                 scope.$emit('hostsReload');
              }
              });

           if (scope.selected.length > 0 ) {
              var host;
              for (var i=0; i < scope.selected.length; i++) {
                  host = null;
                  for (var j=0; j < scope.subhosts.length; j++) {
                      if (scope.subhosts[j].id == scope.selected[i]) {
                         host = scope.subhosts[j];
                      }
                  }
                  if (host !== null) {
                     Rest.post(host)
                         .success( function(data, status, headers, config) {
                             scope.queue.push({ result: 'success', data: data, status: status });
                             scope.$emit('callFinished');
                             })
                         .error( function(data, status, headers, config) {
                             scope.queue.push({ result: 'error', data: data, status: status, headers: headers });
                             scope.$emit('callFinished');
                             });
                  }
              }
           }
           else {
              $('#form-modal').modal('hide');
              scope.$emit('hostsReload');
           }  
           }

        scope.toggle_subhost = function(id) {
           if (scope[list.iterator + "_" + id + "_class"] == "success") {
              scope[list.iterator + "_" + id + "_class"] = "";
              document.getElementById('check_' + id).checked = false;
              if (scope.selected.indexOf(id) > -1) {
                 scope.selected.splice(scope.selected.indexOf(id),1);
              }
           }
           else {
              scope[list.iterator + "_" + id + "_class"] = "success";
              document.getElementById('check_' + id).checked = true;
              if (scope.selected.indexOf(id) == -1) {
                 scope.selected.push(id);
              }
           }
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
                                  $('#form-modal').modal('hide');
                              })
                              .error( function(data, status, headers, config) {
                                  ProcessErrors(scope, data, status, form,
                                     { hdr: 'Error!', msg: 'Failed to add host varaibles. PUT returned status: ' + status });
                              });
                       }
                       else {
                          $('#form-modal').modal('hide');
                          scope.$emit('hostsReload');
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
                                   $('#form-modal').modal('hide');
                                   scope.$emit('hostsReload');
                               })
                               .error( function(data, status, headers, config) {
                                   ProcessErrors(scope, data, status, form,
                                       { hdr: 'Error!', msg: 'Failed to update host varaibles. PUT returned status: ' + status });
                                   });
                        }
                        else {
                           $('#form-modal').modal('hide');
                           scope.$emit('hostsReload');
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
        
        // Delete the selected host. Disassociates it from the group. 
        
        var scope = params.scope;
        var group_id = params.group_id; 
        var inventory_id = params.inventory_id;
        var host_id = params.host_id;
        var host_name = params.host_name; 
        var url = (scope.group_id !== null) ? GetBasePath('groups') + scope.group_id + '/hosts/' : 
            GetBasePath('inventory') + inventory_id + '/hosts/';
        
        var action_to_take = function() {
            if (scope.removeHostsReload) {
               scope.removeHostsReload();
            }
            scope.removeHostsReload = scope.$on('hostsReload', function() {
                HostsReload(params);
                });
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
                       { hdr: 'Error!', msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                   });      
            };

        //Force binds to work. Not working usual way.
        if (scope.group_id !== null) {
           $('#prompt-header').text('Remove Host from Group');
           $('#prompt-body').text('Are you sure you want to remove host ' + host_name + ' from the group?');
        }
        else {
           $('#prompt-header').text('Delete Host');
           $('#prompt-body').text('Are you sure you want to permenantly remove host ' + host_name + '?');
        }
        $('#prompt-action-btn').addClass('btn-danger');
        scope.promptAction = action_to_take;  // for some reason this binds?
        $('#prompt-modal').modal({
            backdrop: 'static',
            keyboard: true,
            show: true
            });
        }
        }])


    .factory('HostsReload', ['RelatedSearchInit', 'RelatedPaginateInit', 'InventoryForm', 'GetBasePath',
    function(RelatedSearchInit, RelatedPaginateInit, InventoryForm, GetBasePath) {
    return function(params) {
        // Rerfresh the Hosts view on right side of page
        scope = params.scope;
        var url = (scope.group_id !== null) ? GetBasePath('groups') + scope.group_id + '/hosts/' :
                  GetBasePath('inventory') + params.inventory_id + '/hosts/';
        var relatedSets = { hosts: { url: url, iterator: 'host' } };
        RelatedSearchInit({ scope: params.scope, form: InventoryForm, relatedSets: relatedSets });
        RelatedPaginateInit({ scope: params.scope, relatedSets: relatedSets });
        params.scope.search('host');
        if (!params.scope.$$phase) {
           params.scope.$digest();
        }
        }
        }]);



