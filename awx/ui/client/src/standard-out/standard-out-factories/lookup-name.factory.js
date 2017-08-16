/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
     ['Rest', 'ProcessErrors', 'Empty', function(Rest, ProcessErrors, Empty) {
         return function(params) {
             var url = params.url,
                 scope_var = params.scope_var,
                 scope = params.scope,
                 callback = params.callback;
             Rest.setUrl(url);
             Rest.get()
                 .success(function(data) {
                     if (scope_var === 'inventory_source') {
                         scope.inventory = data.inventory;
                     }
                     if (!Empty(data.name)) {
                         scope[scope_var + '_name'] = data.name;
                     }

                     if (callback) {
                        scope.$emit(callback, data);
                     }
                 })
                 .error(function(data, status) {
                     if (status === 403 && params.ignore_403) {
                         return;
                     }
                     ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                         msg: 'Failed to retrieve ' + url + '. GET returned: ' + status });
                 });
         };
     }];
