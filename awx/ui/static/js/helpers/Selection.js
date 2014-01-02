/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
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

    .factory('SelectionInit', [ 'Rest', 'Alert', 'ProcessErrors', 'ReturnToCaller', 'Wait',
    function(Rest, Alert, ProcessErrors, ReturnToCaller, Wait) {
    return function(params) {
         
        var scope = params.scope;     // current scope
        var list = params.list;       // list object
        var target_url = params.url;  // URL to POST selected objects
        var returnToCaller = params.returnToCaller;

        if (params.selected !== undefined) {
           var selected = params.selected;
        }
        else { 
           var selected = [];   //array of selected row IDs
        }

        scope.formModalActionDisabled = true;
        scope.disableSelectBtn = true;

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
                      for  (var j=0; j < selected.length; j++) {
                           if (selected[j].id == id) {
                              found = true;
                              break;
                           }
                      }
                      if (!found) {
                         selected.push(scope[list.name][i]);
                      }
                   }
                   else {
                      // unselect the row
                      scope[list.name][i]['checked'] = '0';
                      scope[list.name][i]['success_class'] = '';
                      
                      // remove selected object from the array
                      for  (var j=0; j < selected.length; j++) {
                           if (selected[j].id == id) {
                              selected.splice(j,1);
                              break;
                           }
                      }
                   }
                }
            }
            if (selected.length > 0) {
               scope.formModalActionDisabled = false;
               scope.disableSelectBtn = false;
            }
            else {
               scope.formModalActionDisabled = true;
               scope.disableSelectBtn = true;
            }
            }
        
        // Add the selections
        scope.finishSelection = function() {
            Rest.setUrl(target_url);
            var queue = [];
            scope.formModalActionDisabled = true;
            scope.disableSelectBtn = true;
           
            Wait('start');

            function finished() {
                selected = [];
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
               if (queue.length == selected.length) {
                  Wait('stop');
                  var errors = 0;   
                  for (var i=0; i < queue.length; i++) {
                      if (queue[i].result == 'error') {
                          ProcessErrors(scope, queue[i].data, queue[i].status, null,
                              { hdr: 'POST Failure', msg: 'Failed to add ' + list.iterator + 
                              '. POST returned status: ' + queue[i].status });
                          errors++;
                      }
                 }
                 if (errors == 0) {
                     finished();
                 }
              }
              });

            if (selected.length > 0 ) {
                for (var j=0; j < selected.length; j++) {
                   Rest.post(selected[j])
                       .success( function(data, status, headers, config) {
                           queue.push({ result: 'success', data: data, status: status });
                           scope.$emit('callFinished');
                           })
                       .error( function(data, status, headers, config) {
                           queue.push({ result: 'error', data: data, status: status, headers: headers });
                           scope.$emit('callFinished');
                           });
               }
            }
            else {
               finished();
            }  
            }

        scope.formModalAction = scope.finishSelection;

        // Initialize our data set after a refresh (page change or search)
        if (scope.SelectPostRefreshRemove) {
           scope.SelectPostRefreshRemove();
        }
        scope.SelectPostRefreshRemove = scope.$on('PostRefresh', function() {
            if (scope[list.name]) {
               for (var i=0; i < scope[list.name].length; i++) {
                   var found = false;
                   for (var j=0; j < selected.length; j++) {
                       if (selected[j].id == scope[list.name][i].id) {
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