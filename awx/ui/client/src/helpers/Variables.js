/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 
     /**
 * @ngdoc function
 * @name helpers.function:Variables
 * @description
 *  VariablesHelper
 *
 *
 */

export default
angular.module('VariablesHelper', ['Utilities'])

    /**
     variables: string containing YAML or JSON | a JSON object.

     If JSON string, convert to JSON object and run through jsyaml.safeDump() to create a YAML document. If YAML,
     will attempt to load via jsyaml.safeLoad() and return a YAML document using jsyaml.safeDump(). In all cases
     a YAML document is returned.
    **/
    .factory('ParseVariableString', ['$log', 'ProcessErrors', 'SortVariables', function ($log, ProcessErrors, SortVariables) {
        return function (variables) {
            var result = "---", json_obj;
            if (typeof variables === 'string') {
                if (variables === "{}" || variables === "null" || variables === "" ||  variables === "\"\"") {
                    // String is empty, return ---
                } else {
                    try {
                        json_obj = JSON.parse(variables);
                        json_obj = SortVariables(json_obj);
                        result = jsyaml.safeDump(json_obj);

                    }
                    catch (e) {
                        $log.debug('Attempt to parse extra_vars as JSON failed. Check that the variables parse as yaml.  Set the raw string as the result.');
                        try {
                            // do safeLoad, which well error if not valid yaml
                            json_obj = jsyaml.safeLoad(variables);
                            // but just send the variables
                            result = variables;
                        }
                        catch(e2) {
                            ProcessErrors(null, variables, e2.message, null, { hdr: 'Error!',
                                msg: 'Attempts to parse variables as JSON and YAML failed. Last attempt returned: ' + e2.message });
                        }
                    }
                }
            }
            else {
                if ($.isEmptyObject(variables) || variables === null) {
                    // Empty object, return ---
                }
                else {
                    // convert object to yaml
                    try {
                        json_obj = SortVariables(variables);
                        result = jsyaml.safeDump(json_obj);
                        // result = variables;
                    }
                    catch(e3) {
                        ProcessErrors(null, variables, e3.message, null, { hdr: 'Error!',
                            msg: 'Attempt to convert JSON object to YAML document failed: ' + e3.message });
                    }
                }
            }
            return result;
        };
    }])

    /**
     parseType: 'json' | 'yaml'
     variables: string containing JSON or YAML
     stringify: optional, boolean

     Parse the given string according to the parseType to a JSON object. If stringify true,
     stringify the object and return the string. Otherwise, return the JSON object.

     **/
    .factory('ToJSON', ['$log', 'ProcessErrors', function($log, ProcessErrors) {
        return function(parseType, variables, stringify, reviver) {
            var json_data,
            result,
            tmp;
            // bracketVar,
            // key,
            // lines, i, newVars = [];
            if (parseType === 'json') {
                try {
                    // perform a check to see if the user cleared the field completly
                    if(variables.trim() === "" || variables.trim() === "{" || variables.trim() === "}" ){
                        variables = "{}";
                    }
                    //parse a JSON string
                    if (reviver) {
                        json_data = JSON.parse(variables, reviver);
                    }
                    else {
                        json_data = JSON.parse(variables);
                    }
                }
                catch(e) {
                    json_data = {};
                    $log.error('Failed to parse JSON string. Parser returned: ' + e.message);
                    ProcessErrors(null, variables, e.message, null, { hdr: 'Error!',
                        msg: 'Failed to parse JSON string. Parser returned: ' + e.message });
                    throw  'Parse error. Failed to parse variables.';
                }
            } else {
                try {
                    if(variables.trim() === "" || variables.trim() === "-" || variables.trim() === "--"){
                        variables = '---';
                    }
                    json_data = jsyaml.safeLoad(variables);
                    if(json_data!==null){
                        // unparsing just to make sure no weird characters are included.
                        tmp = jsyaml.dump(json_data);
                        if(tmp.indexOf('[object Object]')!==-1){
                            throw "Failed to parse YAML string. Parser returned' + key + ' : ' +value + '.' ";
                        }
                    }
                }
                catch(e) {
                    json_data = undefined; // {};
                    // $log.error('Failed to parse YAML string. Parser returned undefined');
                    ProcessErrors(null, variables, e.message, null, { hdr: 'Error!',
                        msg: 'Failed to parse YAML string. Parser returned undefined'});
                }
            }
            // Make sure our JSON is actually an object
            if (typeof json_data !== 'object') {
                ProcessErrors(null, variables, null, null, { hdr: 'Error!',
                    msg: 'Failed to parse variables. Attempted to parse ' + parseType + '. Parser did not return an object.' });
                // setTimeout( function() {
                throw  'Parse error. Failed to parse variables.';
                // }, 1000);
            }
            result = json_data;
            if (stringify) {
                if(json_data === undefined){
                    result = undefined;
                }
                else if ($.isEmptyObject(json_data)) {
                    result = "";
                } else {
                    // utilize the parsing to get here
                    // but send the raw variable string
                    result = variables;
                }
            }
            return result;
        };
    }])

    .factory('SortVariables', [ function() {
        return function(variableObj) {
            var newObj;
            function sortIt(objToSort) {
                var i,
                    keys = Object.keys(objToSort),
                    newObj = {};
                keys = keys.sort();
                for (i=0; i < keys.length; i++) {
                    if (typeof objToSort[keys[i]] === 'object' && objToSort[keys[i]] !== null && !Array.isArray(objToSort[keys[i]])) {
                        newObj[keys[i]] = sortIt(objToSort[keys[i]]);
                    }
                    else {
                        newObj[keys[i]] = objToSort[keys[i]];
                    }
                }
                return newObj;
            }
            newObj = sortIt(variableObj);
            return newObj;
        };
    }]);
