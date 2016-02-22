/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

   /**
 * @ngdoc function
 * @name helpers.function:StandardOut
 * @description    Helpers for the standard out views
*/

export default
    angular.module('StandardOutHelper', [])

        .factory('LookUpName', ['Rest', 'ProcessErrors', 'Empty', function(Rest, ProcessErrors, Empty) {
            return function(params) {
                var url = params.url,
                    scope_var = params.scope_var,
                    scope = params.scope;
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data) {
                        if (scope_var === 'inventory_source') {
                            scope[scope_var + '_name'] = data.summary_fields.group.name;
                        }
                        else if (!Empty(data.name)) {
                            scope[scope_var + '_name'] = data.name;
                        }
                        if (!Empty(data.group)) {
                            // Used for inventory_source
                            scope.group = data.group;
                        }
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to retrieve ' + url + '. GET returned: ' + status });
                    });
            };
        }])
