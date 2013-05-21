/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  Hosts.js
 *  
 *  Controller functions for Host model.
 *
 */

'use strict';

function HostsList ($scope, $rootScope, $location, $log, $routeParams, Rest, 
                    Alert, HostList, GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit,
                    ReturnToCaller, ClearScope, ProcessErrors, GetBasePath)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.
   
    var list = HostList
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var defaultUrl = GetBasePath('hosts');
    var view = GenerateList;
    var mode = (base == 'hosts') ? 'edit' : 'select';
    var scope = view.inject(list, { mode: mode });               // Inject our view
    scope.selected = [];
  
    SearchInit({ scope: scope, set: 'hosts', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();
    
    scope.addHost = function() {
       $location.path($location.path() + '/add');
       }

    scope.editHost = function(id) {
       $location.path($location.path() + '/' + id);
       }
 
    scope.deleteHost = function(id, name) {
       
       var action = function() {
           var url = defaultUrl;
           Rest.setUrl(url);
           Rest.post({ id: id, disassociate: 1 })
               .success( function(data, status, headers, config) {
                   $('#prompt-modal').modal('hide');
                   scope.search(list.iterator);
                   })
               .error( function(data, status, headers, config) {
                   $('#prompt-modal').modal('hide');
                   ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                   });      
           };

       Prompt({ hdr: 'Delete', 
                body: 'Are you sure you want to delete host ' + name + '?',
                action: action
                });
       }

    scope.finishSelection = function() {
       var url = ($routeParams.group_id) ? GetBasePath('groups') + $routeParams.group_id + '/hosts/' :
           GetBasePath('inventory') + $routeParams.inventory_id + '/hosts/'; 

       Rest.setUrl(url);  // We're assuming the path matches the api path. 
                                 // Will this always be true??
       scope.queue = [];

       scope.$on('callFinished', function() {
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
             else {
                ReturnToCaller(1);
             }
          }
          });

       if (scope.selected.length > 0 ) {
          var host;
          for (var i=0; i < scope.selected.length; i++) {
              host = null;
              for (var j=0; j < scope.hosts.length; j++) {
                  if (scope.hosts[j].id == scope.selected[i]) {
                     host = scope.hosts[j];
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
          ReturnToCaller(1);
       }  
       }

    scope.toggle_host = function(id) {
       if (scope.selected.indexOf(id) > -1) {
          scope.selected.splice(scope.selected.indexOf(id),1);
       }
       else {
          scope.selected.push(id);
       }
       if (scope[list.iterator + "_" + id + "_class"] == "success") {
          scope[list.iterator + "_" + id + "_class"] = "";
          //$('input[name="check_' + id + '"]').checked = false;
          document.getElementById('check_' + id).checked = false;
       }
       else {
          scope[list.iterator + "_" + id + "_class"] = "success";
          //$('input[name="check_' + id + '"]').checked = true;
          document.getElementById('check_' + id).checked = true;
       }
       }

}

HostsList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'HostList', 'GenerateList', 
                      'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
                      'GetBasePath' ];


function HostsAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, HostForm, 
                   GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, 
                   ClearScope, GetBasePath ) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var defaultUrl = ($routeParams.group_id) ? GetBasePath('groups') + $routeParams.group_id + '/hosts/' : 
       GetBasePath('inventory') + $routeParams.inventory_id + '/hosts/';
   var form = HostForm;
   var generator = GenerateForm;
   var scope = generator.inject(form, {mode: 'add', related: false});
   generator.reset();
   var master = {};

   LoadBreadCrumbs();

   // Save
   scope.formSave = function() {
      Rest.setUrl(defaultUrl);
      var data = {}
      for (var fld in form.fields) {
          if (fld != 'varaibles') {
             data[fld] = scope[fld];
          }  
      }
      if ($routeParams.inventory_id) {
         data['inventory'] = $routeParams.inventory_id;
      }
      try {
          // Make sure we have valid JSON 
          var myjson = JSON.parse(scope.variables);
          Rest.post(data)
              .success( function(data, status, headers, config) {
                  if (scope.variables) {
                     Rest.setUrl(data.related.variable_data);
                     Rest.put({data: scope.variables})
                         .success( function(data, status, headers, config) {
                             ReturnToCaller(1);
                             })
                         .error( function(data, status, headers, config) {
                             ProcessErrors(scope, data, status, form,
                                 { hdr: 'Error!', msg: 'Failed to add host varaibles. POST returned status: ' + status });
                             });
                  }
                  else {
                     ReturnToCaller(1);
                  }
                  })
              .error( function(data, status, headers, config) {
                  ProcessErrors(scope, data, status, form,
                                { hdr: 'Error!', msg: 'Failed to add new host. POST returned status: ' + status });
                  });    
      }
      catch(err) {
           Alert("Error", "Error parsing host variables. Expecting valid JSON. Parser returned " + err);  
      }
      
      };

   // Cancel
   scope.formReset = function() {
      // Defaults
      generator.reset();
      }; 

}

HostsAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'HostForm', 'GenerateForm', 
                     'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'GetBasePath' ]; 


function HostsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, HostForm, 
                    GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, 
                    RelatedPaginateInit, ReturnToCaller, ClearScope, GetBasePath) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   var defaultUrl = GetBasePath('hosts');
   var generator = GenerateForm;
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var form = HostForm;
   var scope = generator.inject(form, {mode: 'edit', related: true});
   generator.reset();
   var master = {};
   var id = $routeParams.host_id;
   var relatedSets = {};

   // After form data loads, load related sets and lookups
   scope.$on('hostLoaded', function() {
       for (var set in relatedSets) {
           scope.search(relatedSets[set].iterator);
       }
       if (scope.variable_url) {
          Rest.setUrl(scope.variable_url);
          Rest.get()
              .success( function(data, status, headers, config) {
                  if ($.isEmptyObject(data.data)) {
                     scope.variables = "\{\}";
                  }
                  else {
                     scope.variables = data.data;
                  }
                  })
              .error( function(data, status, headers, config) {
                  scope.variables = null;
                  ProcessErrors(scope, data, status, form,
                      { hdr: 'Error!', msg: 'Failed to retrieve host variables. GET returned status: ' + status });
                  });
       }
       else {
          scope.variables = "\{\}";
       }
       });

   // Retrieve detail record and prepopulate the form
   Rest.setUrl(defaultUrl + ':id/'); 
   Rest.get({ params: {id: id} })
       .success( function(data, status, headers, config) {
           LoadBreadCrumbs();
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
           // Initialize related search functions. Doing it here to make sure relatedSets object is populated.
           RelatedSearchInit({ scope: scope, form: form, relatedSets: relatedSets });
           RelatedPaginateInit({ scope: scope, relatedSets: relatedSets });
           scope.$emit('hostLoaded');
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
                         { hdr: 'Error!', msg: 'Failed to retrieve host: ' + id + '. GET status: ' + status });
           });
   
   // Save changes to the parent
   scope.formSave = function() {
      Rest.setUrl(defaultUrl + id + '/');
      var data = {}
      for (var fld in form.fields) {
          data[fld] = scope[fld];   
      }

      try { 
         // Make sure we have valid JSON
         var myjson = JSON.parse(scope.variables);
         Rest.put(data)
            .success( function(data, status, headers, config) {
                if (scope.variables) {
                   Rest.setUrl(GetBasePath('hosts') + data.id + '/variable_data/');
                   Rest.put({data: scope.variables})
                       .success( function(data, status, headers, config) {
                           (base == 'hosts') ? ReturnToCaller() : ReturnToCaller(1);
                           })
                       .error( function(data, status, headers, config) {
                           ProcessErrors(scope, data, status, form,
                               { hdr: 'Error!', msg: 'Failed to update host varaibles. PUT returned status: ' + status });
                           });
                }
                else {
                   (base == 'hosts') ? ReturnToCaller() : ReturnToCaller(1);
                }
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, form,
                              { hdr: 'Error!', msg: 'Failed to update host: ' + id + '. PUT status: ' + status });
                });
      }
      catch(err) {
         Alert("Error", "Error parsing host variables. Expecting valid JSON. Parser returned " + err);
      }

      };

   // Cancel
   scope.formReset = function() {
      generator.reset();
      for (var fld in master) {
          scope[fld] = master[fld];
      }
      };

}

HostsEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'HostForm', 
                      'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 
                      'RelatedPaginateInit', 'ReturnToCaller', 'ClearScope', 'GetBasePath' ]; 
  