/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
    function($rootScope, Rest, GetBasePath, ProcessErrors, Wait){
        return {
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
            // data getters
            getInventory: function(id){
                Wait('start');
                this.url = GetBasePath('inventory') + id;
                Rest.setUrl(this.url);
                return Rest.get()
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            getBreadcrumbs: function(groups){
                Wait('start');
                this.url = GetBasePath('groups') + '?' + _.map(groups, function(item){
                    return '&or__id=' + item;
                }).join('');
                Rest.setUrl(this.url);
                return Rest.get()
                    .success(this.success.bind(this))
                    .error(this.error.bind(this));
            },
            // these methods generate a query string to pass to PaginateInit(), SearchInit()
            // always supply trailing slashes and ? prefix
            rootHostsUrl: function(id, failed){
                var url = GetBasePath('inventory') + id + '/hosts' +
                    (failed === 'true' ? '?has_active_failures=true' : '?');
                return url;
            },
            childHostsUrl: function(id, failed){
                var url = GetBasePath('groups') + id + '/all_hosts' +
                    (failed === 'true' ? '?has_active_failures=true' : '?');
                return url;
            },
            childGroupsUrl: function(id){
                var url = GetBasePath('groups') + id + '/children?';
                return url;
            },
            rootGroupsUrl: function(id){
                var url = GetBasePath('inventory') + id+ '/root_groups/';
                return url;
            }
        };
    }];
