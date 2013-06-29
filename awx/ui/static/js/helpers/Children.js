/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  ChildrenHelper
 *
 *  Used in job_events to expand/collapse children
 *
 */
                       
angular.module('ChildrenHelper', ['RestServices', 'Utilities'])  
    .factory('ToggleChildren', ['Alert', 'Rest', 'GetBasePath','ProcessErrors','FormatDate',
    function(Alert, Rest, GetBasePath, ProcessErrors, FormatDate) {
    return function(params) {
        
        var scope = params.scope;
        var list = params.list;
        var id = params.id; 
        var children = params.children; 
        var set = scope[list.name];   // set is now a pointer to scope[list.name]
        
        function calcSpaces(lvl) {
          return lvl * 24;
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
        if (set[clicked]['ngicon'] == 'icon-expand-alt') {
           // Expand: lookup and display children 
           var url = children;
           var search = scope[list.iterator + 'SearchParams'].replace(/^\&/,'').replace(/^\?/,'');
           url += (search) ? '?' + search : "";
           Rest.setUrl(url); 
           Rest.get()
               .success( function(data, status, headers, config) {
                   var found = false;
                   var level = (set[clicked].level !== undefined) ? set[clicked].level + 1 : 1;
                   var spaces = calcSpaces(level); 
                   set[clicked]['ngicon'] = 'icon-collapse-alt';
                   for (var j=0; j < data.results.length; j++) {
                       data.results[j].level = level;
                       data.results[j].spaces = spaces;
                       data.results[j].status = (data.results[j].failed) ? 'error' : 'success';
                       data.results[j].event_display = data.results[j].event_display.replace(/^\u00a0*/g,'');
                       cDate = new Date(data.results[j].created);
                       data.results[j].created = FormatDate(cDate);
                       if (data.results[j].related.children) {
                          data.results[j]['ngclick'] = "toggleChildren(" + data.results[j].id + ", \"" + data.results[j].related.children + "\")";
                          data.results[j]['ngicon'] = 'icon-expand-alt';
                       }
                       if (clicked == (set.length - 1)) {
                          set.push(data.results[j]);
                       }
                       else {
                          set.splice(clicked + 1, 0, data.results[j]);
                       }
                       clicked++;
                   } 
                   scope.$emit('setExpanded', clicked - 1);          
                   })
               .error( function(data, status, headers, config) {
                   ProcessErrors(scope, data, status, null,
                       { hdr: 'Error!', msg: 'Call to ' + children + ' failed. GET returned status: ' + status });
                   });
        }
        else {
           // Collapse: find and remove children
           var parents = [];
           function findChildren(parent, idx) {
              // recursive look through the tree finding all
              // parents including and related the clicked element
              for (var i=idx; i < set.length; i++) {
                  if (set[i].parent == parent) {
                     parents.push(parent);
                     findChildren(set[i].id, i + 1);
                  }
              }
           }
           findChildren(id, clicked + 1);
           // Remove all the children of the clicked element
           var count;
           for (var i=0; i < parents.length; i++) {
               count = 0;
               for (var j=clicked + 1; j< set.length; j++) {
                   if (set[j].parent == parents[i]) {
                      set.splice(j,1);
                      j=clicked; // start back a the top of the list
                   }
               }      
           }
           set[clicked]['ngicon'] = 'icon-expand-alt'; 
        }
    }
    }]);












       
          

        