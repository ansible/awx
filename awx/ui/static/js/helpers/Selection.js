/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  SelectionHelper
 *  Used in list controllers where the list might also be used as a selection list.
 * 
 *  SelectionInit( {
 *      scope: <list scope>,
 *      list: <list object>
 *      })
 */
 
angular.module('SelectionHelper', ['Utilities', 'RestServices'])

    .factory('SelectionInit', [ 'Rest', 'Alert', 'ProcessErrors', 'ReturnToCaller', 
    function(Rest, Alert, ProcessErrors, ReturnToCaller) {
    return function(params) {
         
        var scope = params.scope;     // current scope
        var list = params.list;       // list object
        var target_url = params.url;  // URL to POST selected objects
        var returnToCaller = params.returnToCaller;
        
        scope.selected = [];   //array of selected row IDs
        scope.formModalActionDisabled = true;

        // toggle row selection
        scope['toggle_' + list.iterator] = function(id, ischeckbox) {
            for (var i=0; i < scope[list.name].length; i++) {
                if (scope[list.name][i]['id'] == id) {
                   if ( (scope[list.name][i]['checked'] == '0' && !ischeckbox) || (scope[list.name][i]['checked'] == 1 && ischeckbox) ) {
                      // select the row
                      scope[list.name][i]['checked'] = '1';
                      scope[list.name][i]['success_class'] = 'success';
                      
                      // add selected object to the array
                      var found = false;
                      for  (var j=0; j < scope.selected.length; j++) {
                           if (scope.selected[j].id == id) {
                              found = true;
                              break;
                           }
                      }
                      if (!found) {
                         scope.selected.push(scope[list.name][i]);
                      }
                   }
                   else {
                      // unselect the row
                      scope[list.name][i]['checked'] = '0';
                      scope[list.name][i]['success_class'] = '';
                      
                      // remove selected object from the array
                      for  (var j=0; j < scope.selected.length; j++) {
                           if (scope.selected[j].id == id) {
                              scope.selected.splice(j,1);
                              break;
                           }
                      }
                   }
                }
            }
            if (scope.selected.length > 0) {
               scope.formModalActionDisabled = false; 
            }
            else {
               scope.formModalActionDisabled = true;
            }
            }

        if (target_url) {
           scope.finishSelection = function() {
               Rest.setUrl(target_url);
               scope.queue = [];
               scope.formModalActionDisabled = true;
               
               function finished() {
                   scope.selected = [];
                   if (returnToCaller !== undefined) {
                      ReturnToCaller(returnToCaller);
                   }
                   else {
                      $('#form-modal').modal('hide');
                      scope.$emit('modalClosed');
                   }
                   }
               
               if (scope.callFinishedRemove) {
                  scope.callFinishedRemove();
               }
               scope.callFinishedRemove = scope.$on('callFinished', function() {
                  // We call the API for each selected item. We need to hang out until all the api
                  // calls are finished.
                  if (scope.queue.length == scope.selected.length) {
                     var errors = 0;   
                     for (var i=0; i < scope.queue.length; i++) {
                         if (scope.queue[i].result == 'error') {
                            ProcessErrors(scope, scope.queue[i].data, scope.queue[i].status, null,
                                { hdr: 'POST Failure', msg: 'Failed to add ' + list.iterator + 
                                '. POST returned status: ' + scope.queue[i].status });
                            errors++;
                         }
                     }
                     if (errors == 0) {
                        finished();
                     }
                  }
                  });

               if (scope.selected.length > 0 ) {
                  for (var j=0; j < scope.selected.length; j++) {
                      Rest.post(scope.selected[j])
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
                  finished();
               }  
               }
        }

        scope.formModalAction = scope.finishSelection;

        // Initialize our data set after a refresh
        if (scope.SelectPostRefreshRemove) {
           scope.SelectPostRefreshRemove();
        }
        scope.SelectPostRefreshRemove = scope.$on('PostRefresh', function() {
            if (scope[list.name]) {
               for (var i=0; i < scope[list.name].length; i++) {
                   var found = false;
                   for (var j=0; j < scope.selected.length; j++) {
                       if (scope.selected[j].id == scope[list.name][i].id) {
                          found = true; 
                          break;
                       }
                   }
                   if (found) {
                      scope[list.name][i]['checked'] = '1';
                      scope[list.name][i]['success_class'] = 'success';   
                   }
                   else {
                      scope[list.name][i]['checked'] = '0';
                      scope[list.name][i]['success_class'] = '';
                   }
               }
            }
            });
        }
        }]);