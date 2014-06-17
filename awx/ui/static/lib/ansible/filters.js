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
    // Filter an object of objects by id using an array of id values
    // Created specifically for Filter Events on job detail page.
    //
    .filter('FilterById', [ function() {
        return function(input, list) {
            var results = {};
            if (input && list.length > 0) {
                list.forEach(function(row) {
                    if (input[row]) {
                        results[row] = input[row];
                    }
                });
                return results;
            }
            return input;
        };
    }])

    .filter('FilterByField', [ function() {
        return function(input, list) {
            var fld, key, search = {}, results = {};
            for (fld in list) {
                if (list[fld]) {
                    search[fld] = list[fld];
                }
            }
            if (Object.keys(search).length > 0) {
                for (fld in search) {
                    for (key in input) {
                        if (input[key][fld] === search[fld]) {
                            results[key] = input[key];
                        }
                    }
                }
                return results;
            }
            return input;
        };
    }]);