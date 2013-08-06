/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  GroupsHelper
 *
 *  Routines that handle group add/edit/delete on the Inventory tree widget.
 *  
 */
 
angular.module('GroupsHelper', [ 'RestServices', 'Utilities', 'ListGenerator', 'GroupListDefinition',
                                 'SearchHelper', 'PaginateHelper', 'ListGenerator', 'AuthService', 'GroupsHelper',
                                 'InventoryHelper', 'SelectionHelper'
                                 ])

    .factory('GroupsList', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GroupList', 'GenerateList', 
        'Prompt', 'SearchInit', 'PaginateInit', 'ProcessErrors', 'GetBasePath', 'GroupsAdd', 'RefreshTree', 'SelectionInit',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, GroupList, GenerateList, LoadBreadCrumbs, SearchInit,
        PaginateInit, ProcessErrors, GetBasePath, GroupsAdd, RefreshTree, SelectionInit) {
    return function(params) {
        
        var inventory_id = params.inventory_id;
        var group_id = (params.group_id !== undefined) ? params.group_id : null;

        var list = GroupList;
        var defaultUrl = GetBasePath('inventory') + inventory_id + '/groups/';
        var view = GenerateList;
        
        var scope = view.inject(GroupList, {
            id: 'form-modal-body', 
            mode: 'select',
            breadCrumbs: false,
            selectButton: false 
            });

        scope.formModalActionLabel = 'Select';
        scope.formModalHeader = 'Add Groups';
        scope.formModalCancelShow = true;
        scope.formModalActionClass = 'btn btn-success';
        
        $('.popover').popover('hide');  //remove any lingering pop-overs
        $('#form-modal .btn-none').removeClass('btn-none').addClass('btn-success');
        $('#form-modal').modal({ backdrop: 'static', keyboard: false });

        var url = (group_id) ? GetBasePath('groups') + group_id + '/children/' :
            GetBasePath('inventory') + inventory_id + '/groups/'; 
        SelectionInit({ scope: scope, list: list, url: url });

        if (scope.PostRefreshRemove) {
           scope.PostRefreshRemove();
        }
        scope.PostRefreshRemove = scope.$on('PostRefresh', function() {
            for (var i=0; i < scope.groups.length; i++) {
                if (scope.groups[i].id == group_id) {
                   scope.groups.splice(i,1);
                }
            }
            });

        SearchInit({ scope: scope, set: 'groups', list: list, url: defaultUrl });
        PaginateInit({ scope: scope, list: list, url: defaultUrl, mode: 'lookup' });
        scope.search(list.iterator);

        if (!scope.$$phase) {
           scope.$digest();
        }

        if (scope.removeModalClosed) {
           scope.removeModalClosed();
        }
        scope.removeModalClosed = scope.$on('modalClosed', function() {
            RefreshTree({ scope: scope });
            });

        scope.createGroup = function() {
            $('#form-modal').modal('hide');   
            GroupsAdd({ inventory_id: inventory_id, group_id: group_id });
            }

        }
        }])


    .factory('GroupsAdd', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GroupForm', 'GenerateForm', 
        'Prompt', 'ProcessErrors', 'GetBasePath', 'RefreshTree', 'ParseTypeChange',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, RefreshTree, ParseTypeChange) {
    return function(params) {

        var inventory_id = params.inventory_id;
        var group_id = (params.group_id !== undefined) ? params.group_id : null;

        // Inject dynamic view
        var defaultUrl = (group_id !== null) ? GetBasePath('groups') + group_id + '/children/' : 
            GetBasePath('inventory') + inventory_id + '/groups/';
        var form = GroupForm;
        var generator = GenerateForm;
        var scope = generator.inject(form, {mode: 'add', modal: true, related: false});
        
        scope.formModalActionLabel = 'Save';
        scope.formModalHeader = 'Create Group';
        scope.formModalCancelShow = true;
        scope.parseType = 'yaml';
        ParseTypeChange(scope);

         $('#form-modal').on('hidden.bs.modal', function() {
             var me = $(this);
             $('.modal-backdrop').each(function(index) {
                 $(this).remove();
                 });
             me.unbind('hidden.bs.modal');
             });
        
        $('#form-modal .btn-none').removeClass('btn-none').addClass('btn-success');

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

               if (inventory_id) {
                  data['inventory'] = inventory_id;
               }

               Rest.setUrl(defaultUrl);
               Rest.post(data)
                   .success( function(data, status, headers, config) {
                       if (scope.variables) {
                          Rest.setUrl(data.related.variable_data);
                          Rest.put(json_data)
                              .success( function(data, status, headers, config) {
                                  $('#form-modal').modal('hide');
                                  RefreshTree({ scope: scope });
                              })
                              .error( function(data, status, headers, config) {
                                  ProcessErrors(scope, data, status, form,
                                     { hdr: 'Error!', msg: 'Failed to add group varaibles. PUT returned status: ' + status });
                              });
                       }
                       else {
                          $('#form-modal').modal('hide');
                          RefreshTree({ scope: scope });
                       }
                       })
                   .error( function(data, status, headers, config) {
                       ProcessErrors(scope, data, status, form,
                           { hdr: 'Error!', msg: 'Failed to add new group. POST returned status: ' + status });
                       });
           }
           catch(err) {
               Alert("Error", "Error parsing group variables. Parser returned: " + err);     
           }
           }

        // Cancel
        scope.formReset = function() {
           // Defaults
           generator.reset();
           }; 

        }
        }])


    .factory('GroupsEdit', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GroupForm', 'GenerateForm', 
        'Prompt', 'ProcessErrors', 'GetBasePath', 'RefreshGroupName', 'ParseTypeChange',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, RefreshGroupName, ParseTypeChange) {
    return function(params) {
        
        var group_id = params.group_id;
        var inventory_id = $routeParams.id;
        var generator = GenerateForm;
        var form = GroupForm;
        var defaultUrl =  GetBasePath('groups') + group_id + '/';
        var scope = generator.inject(form, { mode: 'edit', modal: true, related: false});
        generator.reset();
        var master = {};
        var relatedSets = {};

        scope.formModalActionLabel = 'Save';
        scope.formModalHeader = 'Edit Group';
        scope.formModalCancelShow = true;
        scope.parseType = 'yaml';
        ParseTypeChange(scope);

        $('#form-modal .btn-none').removeClass('btn-none').addClass('btn-success');

        // After the group record is loaded, retrieve any group variables
        if (scope.groupLoadedRemove) {
           scope.groupLoadedRemove();
        }
        scope.groupLoadedRemove = scope.$on('groupLoaded', function() {
            for (var set in relatedSets) {
                scope.search(relatedSets[set].iterator);
            }
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
                           { hdr: 'Error!', msg: 'Failed to retrieve group variables. GET returned status: ' + status });
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
                scope.$emit('groupLoaded');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, form,
                    { hdr: 'Error!', msg: 'Failed to retrieve group: ' + id + '. GET status: ' + status });
                });
       
        if (!scope.$$phase) {
           scope.$digest();
        }
        
        // Save changes to the parent
        scope.formModalAction = function() {
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
                
                // Update hosts with new group name/description
                if (master['description'] != data['description'] || 
                    master['name'] != data['name']) {
                    scope.groupTitle = '<h4>' + data['name'] + '</h4>';
                    scope.groupTitle += '<p>' + data['description'] + '</p>';   
                }

                Rest.setUrl(defaultUrl);
                Rest.put(data)
                    .success( function(data, status, headers, config) {
                        if (scope.variables) {
                           //update group variables
                           Rest.setUrl(GetBasePath('groups') + data.id + '/variable_data/');
                           Rest.put(json_data)
                               .success( function(data, status, headers, config) {
                                   $('#form-modal').modal('hide');
                                   RefreshGroupName($('li[group_id="' + group_id + '"]'), scope['name'])
                                   if (refreshHosts) {
                                      scope.$emit('hostsReload');
                                   }
                               })
                               .error( function(data, status, headers, config) {
                                   ProcessErrors(scope, data, status, form,
                                       { hdr: 'Error!', msg: 'Failed to update group varaibles. PUT returned status: ' + status });
                                   });
                        }
                        else {
                           $('#form-modal').modal('hide');
                           RefreshGroupName($('li[group_id="' + group_id + '"]'), scope['name']);
                           if (refreshHosts) {
                              scope.$emit('hostsReload');
                           }
                        }
                        })
                    .error( function(data, status, headers, config) {
                        ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to update group: ' + group_id + '. PUT status: ' + status });
                        });
            }
            catch(err) {
               Alert("Error", "Error parsing group variables. Parser returned: " + err);     
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


    .factory('GroupsDelete', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GroupForm', 'GenerateForm', 
        'Prompt', 'ProcessErrors', 'GetBasePath', 'RefreshTree',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, GroupForm, GenerateForm, Prompt, ProcessErrors,
        GetBasePath, RefreshTree) {
    return function(params) {
        // Delete the selected group node. Disassociates it from its parent.
        var scope = params.scope;
        var group_id = params.group_id; 
        var inventory_id = params.inventory_id; 
        var obj = $('#tree-view li[group_id="' + group_id + '"]');
        var parent = (obj.parent().last().prop('tagName') == 'LI') ? obj.parent().last() : obj.parent().parent().last();
        var url; 
        
        if (parent.attr('type') == 'group') {
           url = GetBasePath('base') + 'groups/' + parent.attr('group_id') + '/children/';
        }
        else {
           url = GetBasePath('inventory') + inventory_id + '/groups/';
        }
        var action_to_take = function() {
            Rest.setUrl(url);
            Rest.post({ id: group_id, disassociate: 1 })
               .success( function(data, status, headers, config) {
                   $('#prompt-modal').modal('hide');
                   RefreshTree({ scope: scope });
                   //$('#tree-view').jstree("delete_node",obj);
                   })
               .error( function(data, status, headers, config) {
                   $('#prompt-modal').modal('hide');
                   RefreshTree({ scope: scope });
                   ProcessErrors(scope, data, status, null,
                       { hdr: 'Error!', msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                   });      
            };
        //Force binds to work. Not working usual way.
        $('#prompt-header').text('Delete Group');
        $('#prompt-body').text('Are you sure you want to remove group ' + $(obj).attr('name') + 
           ' from ' + $(parent).attr('name') + '?');
        $('#prompt-action-btn').addClass('btn-danger');
        scope.promptAction = action_to_take;  // for some reason this binds?
        $('#prompt-modal').modal({
            backdrop: 'static',
            keyboard: true,
            show: true
            });
        }
        }]);



