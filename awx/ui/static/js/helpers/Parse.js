/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  ParseHelper
 *
 *  Routines for parsing variable data and toggling 
 *  between JSON and YAML.
 *
 */

angular.module('ParseHelper', [])  
    .factory('ParseTypeChange', [function() {
    return function(scope, varName, parseTypeName) {

        // Toggle displayed variable string between JSON and YAML

        var fld = (varName) ? varName : 'variables';
        var pfld = (parseTypeName) ? parseTypeName : 'parseType';
        
        scope.blockParseTypeWatch = false; 
        scope.blockVariableDataWatch = false; 

        if (scope['remove' + fld + 'Watch']) {
           scope['remove' + fld + 'Watch']();
        }
        scope['remove' + fld + 'Watch'] = scope.$watch(pfld, function(newVal, oldVal) {
            if (newVal !== oldVal) {
               if (newVal == 'json') {
                  if ( scope[fld] && !/^---$/.test(scope[fld])) { 
                     // convert YAML to JSON
                     try {
                        var json_obj = jsyaml.load(scope[fld]);  //parse yaml into an obj
                        scope[fld] = JSON.stringify(json_obj, null, " ");
                     }
                     catch (err) {
                        // ignore parse errors. allow the user to paste values in and sync the
                        // radio button later. parse errors will be flagged on save.
                     }
                  }
                  else {   
                     scope[fld] = "\{\}";
                  }
               }
               else {
                  if ( scope[fld] && !/^\{\}$/.test(scope[fld]) ) {
                     // convert JSON to YAML
                     try {
                        var json_obj = JSON.parse(scope[fld]);
                        scope[fld] = jsyaml.safeDump(json_obj);
                     }
                     catch (err) {
                        // ignore the errors. allow the user to paste values in and sync the
                        // radio button later. parse errors will be flagged on save.
                     }
                  }
                  else {
                     scope[fld] = "---";
                  }
               }
            }
            });
        }
        }]);
