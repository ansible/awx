/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  Credentials.js
 *  
 *  Controller functions for the Credential model.
 *
 */

'use strict';

function CredentialsList ($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, CredentialList,
                          GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller,
                          ClearScope, ProcessErrors, GetBasePath, SelectionInit)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.
    var list = CredentialList;
    var defaultUrl = GetBasePath('credentials');
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var mode = (base == 'credentials') ? 'edit' : 'select';      // if base path 'credentials', we're here to add/edit
    var scope = view.inject(list, { mode: mode });         // Inject our view
    scope.selected = [];
  
    var url = GetBasePath(base);
       url += (base == 'users') ? $routeParams.user_id + '/credentials/' : $routeParams.team_id + '/credentials/';

    SelectionInit({ scope: scope, list: list, url: url, returnToCaller: 1 });
    
    if (scope.removePostRefresh) {
       scope.removePostRefresh();
    }
    scope.removePostRefresh = scope.$on('PostRefresh', function() {
         // After a refresh, populate the organization name on each row
        for(var i=0; i < scope.credentials.length; i++) {
           if (scope.credentials[i].summary_fields.user) {
              scope.credentials[i].user_username = scope.credentials[i].summary_fields.user.username;
           }
           if (scope.credentials[i].summary_fields.team) {
              scope.credentials[i].team_name = scope.credentials[i].summary_fields.team.name;  
           }
        }
        });

    SearchInit({ scope: scope, set: 'credentials', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();
    
    scope.addCredential = function() {
       $location.path($location.path() + '/add');
       }

    scope.editCredential = function(id) {
       $location.path($location.path() + '/' + id);
       }
 
    scope.deleteCredential = function(id, name) {
       
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

CredentialsList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'CredentialList', 'GenerateList', 
                            'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
                            'GetBasePath', 'SelectionInit'];


function CredentialsAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, CredentialForm, 
                         GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope,
                         GenerateList, SearchInit, PaginateInit, LookUpInit, UserList, TeamList, GetBasePath,
                         GetChoices, Empty, KindChange, OwnerChange) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var defaultUrl = GetBasePath('credentials');
   var form = CredentialForm;
   var generator = GenerateForm;
   var scope = generator.inject(form, {mode: 'add', related: false});
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var defaultUrl = GetBasePath('credentials');
   generator.reset();
   LoadBreadCrumbs();

   // Load the list of options for Kind
   GetChoices({
        scope: scope,
        url: defaultUrl,
        field: 'kind',
        variable: 'credential_kind_options'
        });

   LookUpInit({
       scope: scope,
       form: form,
       current_item: ($routeParams.user_id) ? $routeParams.user_id : null,
       list: UserList, 
       field: 'user' 
       });

   LookUpInit({
       scope: scope,
       form: form,
       current_item: ($routeParams.team_id) ? $routeParams.team_id : null,
       list: TeamList, 
       field: 'team' 
       });

   if (!Empty($routeParams.user_id)) {
      // Get the username based on incoming route
      scope['owner'] = 'user';
      scope['user'] = $routeParams.user_id;
      var url = GetBasePath('users') + $routeParams.user_id + '/';
      Rest.setUrl(url);
      Rest.get()
          .success( function(data, status, headers, config) { 
              scope['user_username'] = data.username;
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, null,
                  { hdr: 'Error!', msg: 'Failed to retrieve user. GET status: ' + status });
              }); 
   }
   else if (!Empty($routeParams.team_id)) {
      // Get the username based on incoming route
      scope['owner'] = 'team';
      scope['team'] = $routeParams.team_id;
      var url = GetBasePath('teams') + $routeParams.team_id + '/';
      Rest.setUrl(url);
      Rest.get()
          .success( function(data, status, headers, config) {
              scope['team_name'] = data.name;
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, null,
                  { hdr: 'Error!', msg: 'Failed to retrieve team. GET status: ' + status });
              });
   }
   
   // Handle Kind change
   scope.kindChange = function () {
       KindChange({ scope: scope, form: form, reset: true });
       }

   // Save
   scope.formSave = function() {
      generator.clearApiErrors();
      
      var data = {}
      for (var fld in form.fields) {
          if (scope[fld] === null) {
             data[fld] = "";
          }
          else {
             data[fld] = scope[fld];
          }
      } 
      
      if (!Empty(scope.team)) {
         data.team = scope.team;
      }
      else {
         data.user = scope.user;
      }

      data['kind'] = scope['kind'].value;

      if (!Empty(data.team) && Empty(data.user)) {
          Alert('Missing User or Team', 'You must provide either a User or a Team. If this credential will only be accessed by a specific ' + 
              'user, select a User. To allow a team of users to access this credential, select a Team.', 'alert-danger');  
      }
      else {
          var url = (!Empty(data.team)) ? GetBasePath('teams') + data.team + '/credentials/' : 
              GetBasePath('users') + data.user + '/credentials/';
          Rest.setUrl(url);
          Rest.post(data)
              .success( function(data, status, headers, config) {
                  var base = $location.path().replace(/^\//,'').split('/')[0];
                  (base == 'credentials') ? ReturnToCaller() : ReturnToCaller(1);
                  })
              .error( function(data, status, headers, config) {
                  ProcessErrors(scope, data, status, form,
                      { hdr: 'Error!', msg: 'Failed to create new Credential. POST status: ' + status });
                  });
      }
      }

   // Handle Owner change
   scope.ownerChange = function() {
       OwnerChange({ scope: scope }); 
       }

   // Reset defaults
   scope.formReset = function() {
      generator.reset();
      };

   // Password change
   scope.clearPWConfirm = function(fld) {
      // If password value changes, make sure password_confirm must be re-entered
      scope[fld] = '';
      scope[form.name + '_form'][fld].$setValidity('awpassmatch', false);
      }

   // Respond to 'Ask at runtime?' checkbox
   scope.ask = function(fld, associated) {
      if (scope[fld + '_ask']) {
         scope[fld] = 'ASK';
         scope[associated] = '';
         scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
      }
      else {
         scope[fld] = '';
         scope[associated] = '';
         scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
      }
      }

   // Click clear button
   scope.clear = function(fld, associated) {
      scope[fld] = '';
      scope[associated] = '';
      scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
      scope[form.name + '_form'].$setDirty();
      }
      
}

CredentialsAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'CredentialForm', 'GenerateForm', 
                           'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'GenerateList',
                           'SearchInit', 'PaginateInit', 'LookUpInit', 'UserList', 'TeamList', 'GetBasePath', 'GetChoices', 'Empty',
                           'KindChange', 'OwnerChange']; 


function CredentialsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, CredentialForm, 
                          GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, 
                          RelatedPaginateInit, ReturnToCaller, ClearScope, Prompt, GetBasePath, GetChoices,
                          KindChange, UserList, TeamList, LookUpInit, Empty, OwnerChange
                          ) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   var defaultUrl=GetBasePath('credentials');
   var generator = GenerateForm;
   var form = CredentialForm;
   var scope = generator.inject(form, {mode: 'edit', related: true});
   generator.reset();
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var defaultUrl = GetBasePath('credentials'); 
   
   var master = {};
   var id = $routeParams.credential_id;
   var relatedSets = {}; 

   function setAskCheckboxes() {
       for (var fld in form.fields) {
           if (form.fields[fld].type == 'password' && scope[fld] == 'ASK') {
              // turn on 'ask' checkbox for password fields with value of 'ASK'
              $("#" + fld + "-clear-btn").attr("disabled","disabled");
              scope[fld + '_ask'] = true;
           }
           else {
              scope[fld + '_ask'] = false;
              $("#" + fld + "-clear-btn").removeAttr("disabled");
           }
           master[fld + '_ask'] = scope[fld + '_ask'];
       }

       // Set kind field to the correct option
       for (var i=0; i < scope['credential_kind_options'].length; i++) {
           if (scope['kind'] == scope['credential_kind_options'][i].value) {
              scope['kind'] = scope['credential_kind_options'][i];
              break;
           }
       }
       } 

   if (scope.removeCredentialLoaded) {
      scope.removeCredentialLoaded();
   }
   scope.removeCredentialLoaded = scope.$on('credentialLoaded', function() {
       LookUpInit({
           scope: scope,
           form: form,
           current_item: ($scope['user_id']) ? scope['user_id'] : null,
           list: UserList, 
           field: 'user' 
           });

       LookUpInit({
           scope: scope,
           form: form,
           current_item: ($scope['team_id']) ? scope['team_id'] : null,
           list: TeamList, 
           field: 'team'
           }); 

       setAskCheckboxes();
       KindChange({ scope: scope, form: form, reset: false });
       });

   if (scope.removeChoicesReady) {
      scope.removeChoicesReady();
   }
   scope.removeChoicesReady = scope.$on('choicesReady', function() {
       // Retrieve detail record and prepopulate the form
       Rest.setUrl(defaultUrl + ':id/'); 
       Rest.get({ params: {id: id} })
           .success( function(data, status, headers, config) {
               LoadBreadCrumbs({ path: '/credentials/' + id, title: data.name });
               for (var fld in form.fields) {
                  if (data[fld] !== null && data[fld] !== undefined) {  
                     scope[fld] = data[fld];
                     master[fld] = scope[fld];
                  }
                  if (form.fields[fld].type == 'lookup' && data.summary_fields[form.fields[fld].sourceModel]) {
                      scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] = 
                          data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                      master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                          scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField];
                  }
               }
               
               if (!Empty(scope['user'])) {
                  scope['owner'] = 'user';
               }
               else {
                  scope['owner'] = 'team';
               }
               master['owner'] = scope['owner']; 

               scope.$emit('credentialLoaded');
               })
           .error( function(data, status, headers, config) {
               ProcessErrors(scope, data, status, form,
                   { hdr: 'Error!', msg: 'Failed to retrieve Credential: ' + $routeParams.id + '. GET status: ' + status });
               });
       });

   GetChoices({
       scope: scope,
       url: defaultUrl,
       field: 'kind',
       variable: 'credential_kind_options',
       callback: 'choicesReady'
       });
 
   // Save changes to the parent
   scope.formSave = function() {
      generator.clearApiErrors();
      
      var data = {}
      for (var fld in form.fields) {
          if (scope[fld] === null) {
             data[fld] = "";
          }
          else {
             data[fld] = scope[fld];
          }
      } 
      
      if (!Empty(scope.team)) {
         data.team = scope.team;
      }
      else {
         data.user = scope.user;
      }

      data['kind'] = scope['kind'].value;

      if (Empty(data.team) && Empty(data.user)) {
          Alert('Missing User or Team', 'You must provide either a User or a Team. If this credential will only be accessed by a specific ' + 
              'user, select a User. To allow a team of users to access this credential, select a Team.', 'alert-danger');  
      }
      else {
          // Save changes to the credential record
          Rest.setUrl(defaultUrl + id + '/');
          Rest.put(data)
              .success( function(data, status, headers, config) {
                  var base = $location.path().replace(/^\//,'').split('/')[0];
                  (base == 'credentials') ? ReturnToCaller() : ReturnToCaller(1);
                  })
              .error( function(data, status, headers, config) {
                  ProcessErrors(scope, data, status, form,
                      { hdr: 'Error!', msg: 'Failed to update Credential. PUT status: ' + status });
                  });
      }
      }
   
   // Handle Owner change
   scope.ownerChange = function() {
       OwnerChange({ scope: scope }); 
       }

   // Handle Kind change
   scope.kindChange = function () {
       KindChange({ scope: scope, form: form, reset: true });
       }

   // Cancel
   scope.formReset = function() {
      generator.reset();
      for (var fld in master) {
          scope[fld] = master[fld];
      }
      setAskCheckboxes();
      };

   // Related set: Add button
   scope.add = function(set) {
      $rootScope.flashMessage = null;
      $location.path('/' + base + '/' + $routeParams.id + '/' + set + '/add');
      };

   // Related set: Edit button
   scope.edit = function(set, id, name) {
      $rootScope.flashMessage = null;
      $location.path('/' + base + '/' + $routeParams.id + '/' + set + '/' + id);
      };

   // Related set: Delete button
   scope['delete'] = function(set, itm_id, name, title) {
      $rootScope.flashMessage = null;
      
      var action = function() {
          var url = defaultUrl + id + '/' + set + '/';
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
          };

       Prompt({ hdr: 'Delete', 
                body: 'Are you sure you want to remove ' + name + ' from ' + scope.name + ' ' + title + '?',
                action: action
                });
       
      }

   // Password change
   scope.clearPWConfirm = function(fld) {
      // If password value changes, make sure password_confirm must be re-entered
      scope[fld] = '';
      scope[form.name + '_form'][fld].$setValidity('awpassmatch', false);
      }
   
   // Respond to 'Ask at runtime?' checkbox
   scope.ask = function(fld, associated) {
      if (scope[fld + '_ask']) {
         $("#" + fld + "-clear-btn").attr("disabled","disabled");
         scope[fld] = 'ASK';
         scope[associated] = '';
         scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
      }
      else {
         $("#" + fld + "-clear-btn").removeAttr("disabled");
         scope[fld] = '';
         scope[associated] = '';
         scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
      }
      }

   scope.clear = function(fld, associated) {
      scope[fld] = '';
      scope[associated] = '';
      scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
      scope[form.name + '_form'].$setDirty();
      }

}

CredentialsEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'CredentialForm', 
                            'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 
                            'RelatedPaginateInit', 'ReturnToCaller', 'ClearScope', 'Prompt', 'GetBasePath', 'GetChoices',
                            'KindChange', 'UserList', 'TeamList', 'LookUpInit', 'Empty', 'OwnerChange' ]; 
  
