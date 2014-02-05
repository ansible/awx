/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * Custom filters 
 *
 */

'use strict';

angular.module('AWFilters', [])
    //
    // capitalize -capitalize the first letter of each word
    //
    .filter('capitalize', [ function() {
        return function(input) {
            var values, result, i;
            if (input) {
                values = input.replace(/\_/g,' ').split(" ");
                result = "";
                for (i = 0; i < values.length; i++){
                    result += values[i].charAt(0).toUpperCase() + values[i].substr(1) + ' ';
                }
                return result.trim();
            }
        };
    }]);