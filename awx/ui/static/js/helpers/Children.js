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

'use strict';

angular.module('ChildrenHelper', ['RestServices', 'Utilities'])
    .factory('ToggleChildren', [ function () {
        return function (params) {

            var scope = params.scope,
                list = params.list,
                id = params.id,
                set = scope[list.name],
                i, clicked, found = false;

            function expand(node) {
                var i;
                set[node].ngicon = 'fa fa-minus-square-o node-toggle';
                for (i = node + 1; i < set.length; i++) {
                    if (set[i].parent === set[node].id) {
                        set[i].show = true;
                    }
                }
            }

            function collapse(node) {
                var i;
                set[node].ngicon = 'fa fa-plus-square-o node-toggle';
                for (i = node + 1; i < set.length; i++) {
                    if (set[i].parent === set[node].id) {
                        set[i].show = false;
                        if (set[i].related.children) {
                            collapse(i);
                        }
                    }
                }
            }

            // Scan the array list and find the clicked element
            for (i = 0; i < set.length && found === false; i++) {
                if (set[i].id === id) {
                    clicked = i;
                    found = true;
                }
            }
            
            // Expand or collapse children based on clicked element's icon
            if (/plus-square-o/.test(set[clicked].ngicon)) {
                // Expand: lookup and display children
                expand(clicked);
            } else if (/minus-square-o/.test(set[clicked].ngicon)) {
                collapse(clicked);
            }
        };
    }
]);