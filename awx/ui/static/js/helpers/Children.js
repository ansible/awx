/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  ChildrenHelper
 *
 */
 /**
 * @ngdoc function
 * @name helpers.function:Children
 * @descriptionUsed in job_events to expand/collapse children by setting the
 *  'show' attribute of each job_event in the set of job_events.
 *  See the filter in job_events.js list.
*/
'use strict';

angular.module('ChildrenHelper', ['RestServices', 'Utilities'])
    .factory('ToggleChildren', ['$location', 'Store', function ($location, Store) {
        return function (params) {

            var scope = params.scope,
                list = params.list,
                id = params.id,
                set = scope[list.name],
                clicked,
                //base = $location.path().replace(/^\//, '').split('/')[0],
                path = $location.path(),
                local_child_store;

            function updateExpand(key, expand) {
                var found = false;
                local_child_store.every(function(child, i) {
                    if (child.key === key) {
                        local_child_store[i].expand = expand;
                        found = true;
                        return false;
                    }
                    return true;
                });
                if (!found) {
                    local_child_store.push({ key: key, expand: expand });
                }
            }

            function updateShow(key, show) {
                var found = false;
                local_child_store.every(function(child, i) {
                    if (child.key === key) {
                        local_child_store[i].show = show;
                        found = true;
                        return false;
                    }
                    return true;
                });
                if (!found) {
                    local_child_store.push({ key: key, show: show });
                }
            }

            function expand(node) {
                var i, has_children = false;
                for (i = node + 1; i < set.length; i++) {
                    if (set[i].parent === set[node].id) {
                        updateShow(set[i].key, true);
                        set[i].show = true;
                    }
                }
                set[node].ngicon = (has_children) ? 'fa fa-minus-square-o node-toggle' : 'fa fa-minus-square-o node-toggle';
            }

            function collapse(node) {
                var i, has_children = false;
                for (i = node + 1; i < set.length; i++) {
                    if (set[i].parent === set[node].id) {
                        set[i].show = false;
                        has_children = true;
                        updateShow(set[i].key, false);
                        if (set[i].related.children) {
                            collapse(i);
                        }
                    }
                }
                set[node].ngicon = (has_children) ? 'fa fa-plus-square-o node-toggle' : 'fa fa-square-o node-toggle';
            }

            local_child_store = Store(path + '_children');
            if (!local_child_store) {
                local_child_store = [];
            }

            // Scan the array list and find the clicked element
            set.every(function(row, i) {
                if (row.id === id) {
                    clicked = i;
                    return false;
                }
                return true;
            });

            // Expand or collapse children based on clicked element's icon
            if (/plus-square-o/.test(set[clicked].ngicon)) {
                // Expand: lookup and display children
                expand(clicked);
                updateExpand(set[clicked].key, true);
            } else if (/minus-square-o/.test(set[clicked].ngicon)) {
                collapse(clicked);
                updateExpand(set[clicked].key, false);
            }
            Store(path + '_children', local_child_store);
        };
    }
]);