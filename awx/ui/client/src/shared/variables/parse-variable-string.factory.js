export default
    function ParseVariableString($log, ProcessErrors, SortVariables) {
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
    }

ParseVariableString.$inject =
    [   '$log',
        'ProcessErrors',
        'SortVariables'
    ];
