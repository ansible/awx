/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  md5helper
 *
 *  Run md5Setup({ scope: , master:, check_field:, default_val: }) 
 *  to initialize md5 fields (checkbox and text field).
 *
 */

angular.module('md5Helper', ['RestServices', 'Utilities'])  
    .factory('md5Setup', ['Alert', 'Rest', 'GetBasePath','ProcessErrors', 
    function(Alert, Rest, GetBasePath, ProcessErrors) {
    return function(params) {
        
        var scope = params.scope;
        var master = params.master; 
        var check_field = params.check_field;
        var default_val = params.default_val;   //default(true/false) for the checkbox
        
        scope[check_field] = default_val;
        master[check_field] = default_val;

        scope.genMD5 = function(fld) {
           var now = new Date();
           scope[fld] = $.md5('AnsibleWorks' + now.getTime());
           }

        scope.toggleCallback = function(fld) {
           if (scope.allow_callbacks == 'false') {
              scope[fld] = '';
           }
           }

        scope.selectAll = function(fld) {
           $('input[name="' + fld +'"]').focus().select();
           }
        
        }
        }]);