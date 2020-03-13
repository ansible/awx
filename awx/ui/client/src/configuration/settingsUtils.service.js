/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$q',
    function($q) {

        return {
            listToArray: function(input) {
                var payload;

                if (input.indexOf('[') !== -1) {
                    payload = JSON.parse(input);

                    if (!Array.isArray(payload)) {
                        payload = [];
                    }
                } else if (input.indexOf('\n') !== -1) {
                    //Parse multiline input
                    payload = input.replace(/^\s+|\s+$/g, "").split('\n');
                } else {
                    if (input === '' || input === '{}') {
                        payload = [];
                    } else {
                        payload = input.replace(/^\s+|\s+$/g, "")
                            .split(/\s*,\s*/);
                    }
                }
                return payload;
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
                if (input !== null && typeof input === 'object') {
                    if (Array.isArray(input)) {
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
                    } else {
                        return JSON.stringify(input);
                    }
                } else {
                    return input;
                }
            },

            imageProcess: function(file) {
                var deferred = $q.defer();
                var SIZELIMIT = 1000000; // 1 MB
                var ACCEPTEDFORMATS = ['image/png', 'image/gif', 'image/jpeg']; //Basic check

                if(file.size < SIZELIMIT && ACCEPTEDFORMATS.indexOf(file.type) !== -1) {
                    var reader = new FileReader();
                    reader.readAsDataURL(file);
                    reader.onload = function () {
                        deferred.resolve(reader.result);
                    };
                    reader.onerror = function () {
                        deferred.reject('File could not be parsed');
                    };
                } else {
                    var error = 'Error: ';
                    if(file.size > SIZELIMIT) {
                        error += 'Must be under ' + SIZELIMIT / 1000000 + 'MB. ';
                    }
                    if(ACCEPTEDFORMATS.indexOf(file.type) === -1) {
                        error += 'Wrong file type - must be png, gif, or jpg.';
                    }
                    deferred.reject(error);
                }
                return deferred.promise;
            }

        };
    }
];
