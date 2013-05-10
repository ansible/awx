/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * Custom directives for form validation 
 *
 */

angular.module('AWDirectives', [])
    
    // awpassmatch:  Add to password_confirm field. Will test if value
    //               matches that of 'input[name="password"]'
    .directive('awpassmatch', function() {
        return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift( function(viewValue) {
                var associated = attrs.awpassmatch;
                var password = $('input[name="' + associated + '"]').val(); 
                if (viewValue == password) {
                   // it is valid
                   ctrl.$setValidity('awpassmatch', true);
                   return viewValue;
                } else {
                   // it is invalid, return undefined (no model update)
                   ctrl.$setValidity('awpassmatch', false);
                   return undefined;
                }
                });
            }
        }
        })
    
    // caplitalize  Add to any input field where the first letter of each
    //              word should be capitalized. Use in place of css test-transform.
    //              For some reason "text-transform: capitalize" in breadcrumbs
    //              causes a break at each blank space. And of course, 
    //              "autocapitalize='word'" only works in iOS. Use this as a fix.
    .directive('capitalize', function() {
        return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift( function(viewValue) {
                var values = viewValue.split(" ");
                var result = "";
                for (i = 0; i < values.length; i++){
                    result += values[i].charAt(0).toUpperCase() + values[i].substr(1) + ' ';
                }
                result = result.trim();
                if (result != viewValue) {
                   ctrl.$setViewValue(result);
                   ctrl.$render();
                }
                return result;
                });
            }
        }
        });