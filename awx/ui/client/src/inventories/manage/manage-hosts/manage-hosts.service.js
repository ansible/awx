/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', 
    function($rootScope, Rest, GetBasePath, ProcessErrors){
        return {
            stringifyParams: function(params){
                return  _.reduce(params, (result, value, key) => {
                    return result + key + '=' + value + '&';
                }, '');
            },
            get: function(params){
                var url = GetBasePath('hosts') + '?' + this.stringifyParams(params);
                Rest.setUrl(url);
                return Rest.get()
                    .success(function(res){
                        return res;
                    })
                    .error(function(data, status) {
                        ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                    });
            },
            post: function(params){
                var url = GetBasePath('hosts');
                Rest.setUrl(url);
                return Rest.post(params)
                    .success(function(res){
                        return res;
                    })
                    .error(function(data, status) {
                        ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                    });
            },
            put: function(host){
                var url = GetBasePath('hosts') + host.id;
                Rest.setUrl(url);
                return Rest.put(host)
                    .success(function(res){
                        return res;
                    })
                    .error(function(data, status) {
                        ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                    });
            }
        };
    }];