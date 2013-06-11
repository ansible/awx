/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  ParseHelper
 *
 *  Routines for parsing variable data and toggling 
 *  between JSON and YAML.
 *
 */

angular.module('ParseHelper', [])  
    .factory('ParseTypeChange', [function() {
    return function(scope) {

        // Toggle displayed variable string between JSON and YAML
        
        scope.blockParseTypeWatch = false; 
        scope.blockVariableDataWatch = false; 

        if (scope.removeParseTypeWatch) {
           scope.removeParseTypeWatch();
        }
        scope.removeParseTypeWatch = scope.$watch('parseType', function(newVal, oldVal) {
            if (newVal !== oldVal) {
               if (newVal == 'json') {
                  if ( scope.variables && !/^---$/.test(scope.variables)) { 
                     // convert YAML to JSON
                     try {
                        var json_obj = jsyaml.load(scope.variables);  //parse yaml into an obj
                        scope.variables = JSON.stringify(json_obj, null, " ");
                     }
                     catch (err) {
                        // ignore parse errors. allow the user to paste values in and sync the
                        // radio button later. parse errors will be flagged on save.
                     }
                  }
                  else {   
                     scope.variables = "\{\}";
                  }
               }
               else {
                  if ( scope.variables && !/^\{\}$/.test(scope.variables) ) {
                     // convert JSON to YAML
                     try {
                        var json_obj = JSON.parse(scope.variables);
                        scope.variables = jsyaml.safeDump(json_obj);
                     }
                     catch (err) {
                        // ignore the errors. allow the user to paste values in and sync the
                        // radio button later. parse errors will be flagged on save.
                     }
                  }
                  else {
                     scope.variables = "---";
                  }
               }
            }
            });
        }
        }]);
