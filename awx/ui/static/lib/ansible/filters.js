/*********************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * Custom filters
 *
 */

'use strict';

angular.module('AWFilters', [])

    //
    // capitalize -capitalize the first letter of each word
    //
    .filter('capitalize', [ function () {
        return function (input) {
            var values, result, i;
            if (input) {
                values = input.replace(/\_/g, ' ').split(" ");
                result = "";
                for (i = 0; i < values.length; i++) {
                    result += values[i].charAt(0).toUpperCase() + values[i].substr(1) + ' ';
                }
                return result.trim();
            }
        };
    }])
    
    //
    // Filter a list of objects by id using an array of id values
    // Created specifically for Filter Events on job detail page.
    //
    .filter('FilterById', [ function() {
        return function(input, list) {
            var found, results = [];
            if (list.length > 0) {
                input.forEach(function(row) {
                    found = false;
                    list.every(function(id) {
                        if (row.id === id) {
                            found = true;
                            return false;
                        }
                        return true;
                    });
                    if (found) {
                        results.push(row);
                    }
                });
                return results;
            }
            return input;
        };
    }]);