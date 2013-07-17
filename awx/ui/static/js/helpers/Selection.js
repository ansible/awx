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
 
angular.module('SelectionHelper', [])  
    .factory('SelectionInit', [ function() {
    return function(params) {
         
        var scope = params.scope;  // form scope
        var list = params.list;    // list object
        
        scope.selected = [];   //array of selected row IDs

        // toggle row selection
        scope['toggle_' + list.iterator] = function(id) {
            for (var i=0; i < scope[list.name].length; i++) {
                if (scope[list.name][i]['id'] == id) {
                   if (scope[list.name][i]['checked'] == '0') {
                      // select the row
                      scope[list.name][i]['checked'] = '1';
                      scope[list.name][i]['success_class'] = 'success';
                      if (scope.selected.indexOf(id) == -1) {
                         // add id to the array
                         scope.selected.push(id);
                      }
                   }
                   else {
                      // unselect the row
                      scope[list.name][i]['checked'] = '0';
                      scope[list.name][i]['success_class'] = '';
                      if (scope.selected.indexOf(id) > -1) {
                         // remove id from the array
                         scope.selected.splice(scope.selected.indexOf(id),1);
                      }
                   }
                }
            }
            }

        // Initialize our data set after a refresh
        if (scope.SelectPostRefreshRemove) {
           scope.SelectPostRefreshRemove();
        }
        scope.SelectPostRefreshRemove = scope.$on('PostRefresh', function() {
            scope.selected = [];
            for (var i=0; i < scope[list.name].length; i++) {
                scope[list.name][i]['checked'] = '0';
                scope[list.name][i]['success_class'] = '';
            }
            });
        }
        }]);