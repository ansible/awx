/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  ChildrenHelper
 *
 *  Used in job_events to expand/collapse children by setting the 
 *  'show' attribute of each job_event in the set of job_events.
 *  See the filter in job_events.js list.
 *
 */
                       
angular.module('ChildrenHelper', ['RestServices', 'Utilities'])  
    .factory('ToggleChildren', ['Alert', 'Rest', 'GetBasePath','ProcessErrors','FormatDate',
    function(Alert, Rest, GetBasePath, ProcessErrors, FormatDate) {
    return function(params) {
        
        var scope = params.scope;
        var list = params.list;
        var id = params.id; 
        var set = scope[list.name];   // set is now a pointer to scope[list.name]
        
        function expand(node) {
           set[node]['ngicon'] = 'fa fa-minus-square-o node-toggle'; 
           for (var i = node + 1; i < set.length; i++) {
               if (set[i].parent == set[node].id) {
                  set[i]['show'] = true;
                  //if (set[i].related.children) {
                  //   expand(i);
                  //}
               }
           }
        }

        function collapse(node) {
           set[node]['ngicon'] = 'fa fa-plus-square-o node-toggle';
           for (var i = node + 1; i < set.length; i++) {
               if (set[i].parent == set[node].id) {
                  set[i]['show'] = false;
                  if (set[i]['related']['children']) {
                      collapse(i);
                  }
               }
           }
        }

        // Scan the array list and find the clicked element
        var clicked;
        var found = false;
        for (var i = 0; i < set.length && found == false; i++){
            if (set[i].id == id) {
               clicked = i;
               found = true;
            }
        }
        // Expand or collapse children based on clicked element's icon
        if (/plus-square-o/.test(set[clicked]['ngicon'])) {
           // Expand: lookup and display children
           expand(clicked);
        }
        else if (/minus-square-o/.test(set[clicked]['ngicon'])) {
           collapse(clicked);
        }
    }
    }]);












       
          

        