/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
    function($rootScope, Rest, GetBasePath, ProcessErrors, Wait){
        return {
            stringifyParams: function(params){
                return  _.reduce(params, (result, value, key) => {
                    return result + key + '=' + value + '&';
                }, '');
            },
            // cute abstractions via fn.bind()
            url: function(){
                return '';
            },
            error: function(data, status) {
                ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                msg: 'Call to ' + this.url + '. GET returned: ' + status });
            },
            success: function(data){
                return data;
            },
            // HTTP methods
            get: function(params){
                Wait('start');
                this.url = GetBasePath('hosts') + '?' + this.stringifyParams(params);
                Rest.setUrl(this.url);
                return Rest.get()
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            post: function(host){
                Wait('start');
                this.url = GetBasePath('hosts');
                Rest.setUrl(this.url);
                return Rest.post(host)
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            put: function(host){
                Wait('start');
                this.url = GetBasePath('hosts') + host.id;
                Rest.setUrl(this.url);
                return Rest.put(host)
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            delete: function(id){
                Wait('start');
                this.url = GetBasePath('hosts') + id;
                Rest.setUrl(this.url);
                return Rest.destroy()
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            }
        };
    }];
