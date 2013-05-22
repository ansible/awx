/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  Admins.js
 *  
 *  Controller functions for ading Admins to an Organization.
 *
 */

'use strict';

function AdminsList ($scope, $rootScope, $location, $log, $routeParams, Rest, 
                     Alert, AdminList, GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit,
                     ReturnToCaller,GetBasePath)
{
    var list = AdminList;
    var defaultUrl = GetBasePath('organizations') + $routeParams.organization_id + '/users/' ;
    var view = GenerateList;
    var mode = 'select';
    var scope = view.inject(AdminList, { mode: mode });         // Inject our view
    scope.selected = [];

    SearchInit({ scope: scope, set: 'admins', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();
    
    scope.finishSelection = function() {
       var url = GetBasePath('organizations') + $routeParams.organization_id + '/admins/'
       Rest.setUrl(url);
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
              for (var j=0; j < scope.admins.length; j++) {
                  if (scope.admins[j].id == scope.selected[i]) {
                     user = scope.admins[j];
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
          ReturnToCaller(1);
       }  
       }

    scope.toggle_admin = function(id) {
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

AdminsList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'AdminList', 'GenerateList', 
                       'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'GetBasePath'];

