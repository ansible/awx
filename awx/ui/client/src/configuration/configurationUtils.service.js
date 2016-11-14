/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    function() {

        return {
            listToArray: function(input) {
                if (input.indexOf('\n') !== -1) {
                    //Parse multiline input
                    return input.replace(/^\s+|\s+$/g, "").split('\n');
                } else {
                    return input.replace(/^\s+|\s+$/g, "").split(/\s*,\s*/);
                }
            },

            arrayToList: function(input) {
                var multiLineInput = false;
                _.each(input, function(statement) {
                    if (statement.indexOf(',') !== -1) {
                        multiLineInput = true;
                    }
                });
                if (multiLineInput === false) {
                    return input.join(', ');
                } else {
                    return input.join('\n');
                }
            },

            isEmpty: function(map) {
                for (var key in map) {
                    if (map.hasOwnProperty(key)) {
                        return false;
                    }
                }
                return true;
            },

            formatPlaceholder: function(input) {
                if(input !== null && typeof input === 'object') {
                    if(Array.isArray(input)) {
                        var multiLineInput = false;
                        _.each(input, function(statement) {
                            if(statement.indexOf(',') !== -1) {
                                multiLineInput = true;
                            }
                        });
                        if(multiLineInput === false) {
                            return input.join(', ');
                        } else {
                            return input.join('\n');
                        }
                    } else {
                        return JSON.stringify(input);
                    }
                } else {
                    return input;
                }
            }

        };
    }
];
