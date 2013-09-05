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
                    ReturnToCaller, ClearScope, ProcessErrors, GetBasePath, SelectionInit)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.

    var list = UserList;
    var defaultUrl = GetBasePath('users');
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
    
    var url = (base == 'organizations') ? GetBasePath('organizations') + $routeParams.organization_id + '/users/' :
        GetBasePath('teams') + $routeParams.team_id + '/users/';
    SelectionInit({ scope: scope, list: list, url: url, returnToCaller: 1 });
    
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
}

UsersList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'UserList', 'GenerateList', 
                      'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
                      'GetBasePath', 'SelectionInit'];


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
      if (scope.organization !== undefined && scope.organization !== null && scope.organization !== '') {
         Rest.setUrl(defaultUrl + scope.organization + '/users/');
             var data = {}
             for (var fld in form.fields) {
                 if (form.fields[fld].realName) {
                    data[form.fields[fld].realName] = scope[fld];
                 }
                 else {
                    data[fld] = scope[fld];
                 }   
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
      }
      else {
         scope.organization_name_api_error = 'A value is required';
      }
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

   scope.PermissionAddAllowed =  false; 

   // After the Organization is loaded, retrieve each related set
   scope.$on('userLoaded', function() {
       for (var set in relatedSets) {
           scope.search(relatedSets[set].iterator);
       }
       CheckAccess({ scope: scope });  //Does the user have access add Permissions?
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
         if (scope.PermissionAddAllowed) {
            $location.path('/' + base + '/' + $routeParams.user_id + '/' + set + '/add');  
         }
         else {
            Alert('Access Denied', 'You do not have access to this function. Please contact your system administrator.');
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
         if (scope.PermissionAddAllowed) {
            $location.path('/users/' + $routeParams.user_id + '/permissions/' + id);
         }
         else {
            Alert('Access Denied', 'You do not have access to this function. Please contact your system administrator.');
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
             if (scope.PermissionAddAllowed) {
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
              else {
                 Alert('Access Denied', 'You do not have access to this function. Please contact your system administrator.'); 
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
  
