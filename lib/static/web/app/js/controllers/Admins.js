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
                     ReturnToCaller)
{
    var list = AdminList;
    var defaultUrl = '/api/v1' + '/organizations/' + $routeParams.id + '/users/' ;
    var view = GenerateList;
    //var paths = $location.path().replace(/^\//,'').split('/');
    var mode = 'select';
    var scope = view.inject(AdminList, { mode: mode });         // Inject our view
    scope.selected = [];

    SearchInit({ scope: scope, set: 'admins', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();
    
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
                    // there is no way to know which user raised the error. no data comes
                    // back from the api call. 
                    //   $('td.username-column').each(function(index) {
                    //      if ($(this).text() == scope.queue[i].username) {
                    //         $(this).addClass("error");
                    //      }
                    //   });
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
          for (var i=0; i < scope.selected.length; i++) {
              //var admin = scope.admins[scope.selected[i]].username;
              Rest.post(scope.admins[scope.selected[i]])
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
       else {
          returnToCaller();
       }  
       }

    scope.toggle_admin = function(idx) {
       if (scope.selected.indexOf(idx) > -1) {
          scope.selected.splice(scope.selected.indexOf(idx),1);
       }
       else {
          scope.selected.push(idx);
       }
       }
}

AdminsList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'AdminList', 'GenerateList', 
                       'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller' ];

