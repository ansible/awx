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
        if (input) {
            var values = input.replace(/\_/g,' ').split(" ");
            var result = "";
            for (var i = 0; i < values.length; i++){
                result += values[i].charAt(0).toUpperCase() + values[i].substr(1) + ' ';
            }
            return result.trim();
        }
        }
        }]);