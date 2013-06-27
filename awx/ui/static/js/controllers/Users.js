/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  Users.js
 *  
 *  Controller functions for User model.
 *
 */

'use strict';

function UsersList ($scope, $rootScope, $location, $log, $routeParams, Rest, 
                    Alert, UserList, GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit,
                    ReturnToCaller, ClearScope, ProcessErrors)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                              //scope.

    var list = UserList;
    var defaultUrl = '/api/v1/users/';
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var mode = (base == 'users') ? 'edit' : 'select';      // if base path 'users', we're here to add/edit users
    var scope = view.inject(UserList, { mode: mode });         // Inject our view
    scope.selected = [];

    $rootScope.flashMessage = null;
    SearchInit({ scope: scope, set: 'users', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);


    LoadBreadCrumbs();
    
    scope.addUser = function() {
       $location.path($location.path() + '/add');
       }

    scope.editUser = function(id) {
       $location.path($location.path() + '/' + id);
       }
 
    scope.deleteUser = function(id, name) {
       
       var action = function() {
           var url = defaultUrl + id + '/';
           Rest.setUrl(url);
           Rest.destroy()
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
                body: 'Are you sure you want to delete ' + name + '?',
                action: action
                });
       }

    scope.finishSelection = function() {
       Rest.setUrl('/api/v1' + $location.path() + '/');  // We're assuming the path matches the api path. 
                                                         // Will this always be true??
       scope.queue = [];

       scope.$on('callFinished', function() {
          // We call the API for each selected user. We need to hang out until all the api
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
                Alert('Error', 'There was an error while adding one or more of the selected users.');  
             }
             else {
                ReturnToCaller(1);
             }
          }
          });

       if (scope.selected.length > 0 ) {
          var user;
          for (var i=0; i < scope.selected.length; i++) {
              user = null;
              for (var j=0; j < scope.users.length; j++) {
                  if (scope.users[j].id == scope.selected[i]) {
                     user = scope.users[j];
                  }
              }
              if (user !== null) {
                 Rest.post(user)
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
          ReturnToCaller();
       }  
       }

    scope.toggle_user = function(id) {
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
}

UsersList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'UserList', 'GenerateList', 
                      'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors'
                      ];


function UsersAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, UserForm, 
                   GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope,
                   GetBasePath, LookUpInit, OrganizationList) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var defaultUrl = GetBasePath('organizations');
   var form = UserForm;
   var generator = GenerateForm;
   var scope = generator.inject(form, {mode: 'add', related: false});
   generator.reset();

   LoadBreadCrumbs();

   // Configure the lookup dialog. If we're adding a user through the Organizations tab, 
   // default the Organization value.
   LookUpInit({
       scope: scope,
       form: form,
       current_item: ($routeParams.organization_id !== undefined) ? $routeParams.organization_id : null,
       list: OrganizationList, 
       field: 'organization' 
       });

   if ($routeParams.organization_id) {
      scope.organization = $routeParams.organization_id;
      Rest.setUrl(GetBasePath('organizations') + $routeParams.organization_id + '/');
      Rest.get()
          .success( function(data, status, headers, config) {
              scope['organization_name'] = data.name;
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                  { hdr: 'Error!', msg: 'Failed to lookup Organization: ' + data.id + '. GET returned status: ' + status });
              });
   }

   // Save
   scope.formSave = function() {
      Rest.setUrl(defaultUrl + scope.organization + '/users/');
      var data = {}
      for (var fld in form.fields) {
          data[fld] = scope[fld];   
      } 
      Rest.post(data)
          .success( function(data, status, headers, config) {
              var base = $location.path().replace(/^\//,'').split('/')[0];
              if (base == 'users') {
                $rootScope.flashMessage = 'New user successfully created!';
                $location.path('/users/' + data.id);
              }
              else {
                ReturnToCaller(1);
              }
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                  { hdr: 'Error!', msg: 'Failed to add new user. POST returned status: ' + status });
              });
      };

   // Cancel
   scope.formReset = function() {
      // Defaults
      generator.reset();
      }; 

   // Password change
   scope.clearPWConfirm = function(fld) {
      // If password value changes, make sure password_confirm must be re-entered
      scope[fld] = '';
      scope[form.name + '_form'][fld].$setValidity('awpassmatch', false);
      }
}

UsersAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'UserForm', 'GenerateForm', 
                     'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'GetBasePath', 
                     'LookUpInit', 'OrganizationList' ]; 


function UsersEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, UserForm, 
                    GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, 
                    RelatedPaginateInit, ReturnToCaller, ClearScope, GetBasePath, Prompt, CheckAccess) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   var defaultUrl=GetBasePath('users');
   var generator = GenerateForm;
   var form = UserForm;
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var scope = generator.inject(form, {mode: 'edit', related: true});
   generator.reset();
   var master = {};
   var id = $routeParams.user_id;
   var relatedSets = {}; 

   // After the Organization is loaded, retrieve each related set
   scope.$on('userLoaded', function() {
       for (var set in relatedSets) {
           scope.search(relatedSets[set].iterator);
       }
       });

   // Retrieve detail record and prepopulate the form
   Rest.setUrl(defaultUrl + ':id/'); 
   Rest.get({ params: {id: id} })
       .success( function(data, status, headers, config) {
           LoadBreadCrumbs({ path: '/users/' + id, title: data.username });
           for (var fld in form.fields) {
              if (data[fld]) {
                 if (fld == 'is_superuser') {
                    scope[fld] = (data[fld] == 'true' || data[fld] == true) ? 'true' : 'false';
                 }
                 else {
                    scope[fld] = data[fld];
                 }  
                 master[fld] = scope[fld];
              }
           }
           var related = data.related;
           for (var set in form.related) {
               if (related[set]) {
                  relatedSets[set] = { url: related[set], iterator: form.related[set].iterator };
               }
           }

           // Initialize related search functions. Doing it here to make sure relatedSets object is populated.
           RelatedSearchInit({ scope: scope, form: form, relatedSets: relatedSets });
           RelatedPaginateInit({ scope: scope, relatedSets: relatedSets });
           scope.$emit('userLoaded');
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
                         { hdr: 'Error!', msg: 'Failed to retrieve user: ' + $routeParams.id + '. GET status: ' + status });
           });
   
   // Save changes to the parent
   scope.formSave = function() {
      $rootScope.flashMessage = null;
      Rest.setUrl(defaultUrl + id + '/');
      var data = {}
      for (var fld in form.fields) {
          data[fld] = scope[fld];   
      } 
      Rest.put(data)
          .success( function(data, status, headers, config) {
              var base = $location.path().replace(/^\//,'').split('/')[0];
              (base == 'users') ? ReturnToCaller() : ReturnToCaller(1);
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to update users: ' + $routeParams.id + '. PUT status: ' + status });
              });
      };

   // Cancel
   scope.formReset = function() {
      $rootScope.flashMessage = null;
      generator.reset();
      for (var fld in master) {
          scope[fld] = master[fld];
      }
      };

   // Password change
   scope.clearPWConfirm = function(fld) {
      // If password value changes, make sure password_confirm must be re-entered
      scope[fld] = '';
      scope[form.name + '_form'][fld].$setValidity('awpassmatch', false);
      $rootScope.flashMessage = null;
      }


   // Related set: Add button
   scope.add = function(set) {
      $rootScope.flashMessage = null;
      if (set == 'permissions') {
         if (CheckAccess()) {
            $location.path('/' + base + '/' + $routeParams.user_id + '/' + set + '/add');  
         }
      }
      else {
         $location.path('/' + base + '/' + $routeParams.user_id + '/' + set);
      }
      };

   // Related set: Edit button
   scope.edit = function(set, id, name) {
      $rootScope.flashMessage = null;
      if (set == 'permissions') {
         if (CheckAccess()) {
            $location.path('/users/' + $routeParams.user_id + '/permissions/' + id);
         }
      }
      else {
         $location.path('/' + set + '/' + id);
      }
      };

   // Related set: Delete button
   scope['delete'] = function(set, itm_id, name, title) {
      $rootScope.flashMessage = null;
      
      var action = function() {
          var url;
          if (set == 'permissions') {
             if (CheckAccess()) {
                url = GetBasePath('base') + 'permissions/' + itm_id + '/';
                Rest.setUrl(url);
                Rest.destroy()
                    .success( function(data, status, headers, config) {
                        $('#prompt-modal').modal('hide');
                        scope.search(form.related[set].iterator);
                        })
                    .error( function(data, status, headers, config) {
                        $('#prompt-modal').modal('hide');
                        ProcessErrors(scope, data, status, null,
                          { hdr: 'Error!', msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                        });
              }   
          }
          else {
              url = defaultUrl + $routeParams.user_id + '/' + set + '/';
              Rest.setUrl(url);
              Rest.post({ id: itm_id, disassociate: 1 })
                  .success( function(data, status, headers, config) {
                      $('#prompt-modal').modal('hide');
                      scope.search(form.related[set].iterator);
                      })
                  .error( function(data, status, headers, config) {
                      $('#prompt-modal').modal('hide');
                      ProcessErrors(scope, data, status, null,
                          { hdr: 'Error!', msg: 'Call to ' + url + ' failed. POST returned status: ' + status });
                      });      
          }
          }

       Prompt({ hdr: 'Delete', 
                body: 'Are you sure you want to remove ' + name + ' from ' + scope.username + ' ' + title + '?',
                action: action
                });
      }

}

UsersEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'UserForm', 
                      'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 
                      'RelatedPaginateInit', 'ReturnToCaller', 'ClearScope', 'GetBasePath', 'Prompt', 'CheckAccess']; 
  
