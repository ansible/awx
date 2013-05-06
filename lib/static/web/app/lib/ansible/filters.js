/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * Custom filters 
 *
 */
 
angular.module('AWFilters', [])
    //
    // capitalize -capitalize the first letter of each word
    //
    .filter('capitalize', function() {
    return function(input) {
        var values = input.split(" ");
        var result = "";
        for (i = 0; i < values.length; i++){
            result += values[i].charAt(0).toUpperCase() + values[i].substr(1) + ' ';
        }
        result = result.trim();
        return result;
        }
        });