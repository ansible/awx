export default
    function ToJSON($log, ProcessErrors) {
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
    }

ToJSON.$inject =
    [   '$log',
        'ProcessErrors'
    ];
