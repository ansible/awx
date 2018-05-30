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
                    .then(this.success.bind(this))
                    .catch(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            getBreadcrumbs: function(groups){
                Wait('start');
                this.url = GetBasePath('groups') + '?' + _.map(groups, function(item){
                    return '&or__id=' + item;
                }).join('');
                Rest.setUrl(this.url);
                return Rest.get()
                    .then(this.success.bind(this))
                    .catch(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            rootHostsUrl: function(id){
                var url = GetBasePath('inventory') + id + '/hosts';
                return url;
            },
            childHostsUrl: function(id){
                var url = GetBasePath('groups') + id + '/all_hosts';
                return url;
            },
            childGroupsUrl: function(id){
                var url = GetBasePath('groups') + id + '/children';
                return url;
            },
            groupsUrl: function(id){
                var url = GetBasePath('inventory') + id+ '/groups';
                return url;
            },
            inventorySourcesOptions: function(inventoryId) {
                this.url = GetBasePath('inventory') + inventoryId + '/inventory_sources';
                Rest.setUrl(this.url);
                return Rest.options()
                    .then(this.success.bind(this))
                    .catch(this.error.bind(this));
            },
            updateInventorySourcesGet: function(inventoryId) {
                this.url = GetBasePath('inventory') + inventoryId + '/update_inventory_sources';
                Rest.setUrl(this.url);
                return Rest.get()
                    .then(this.success.bind(this))
                    .catch(this.error.bind(this));
            },
            getHost: function(inventoryId, hostId) {
                this.url = GetBasePath('inventory') + inventoryId + '/hosts?id=' + hostId;
                Rest.setUrl(this.url);
                return Rest.get()
                    .then(this.success.bind(this))
                    .catch(this.error.bind(this));
            }
        };
    }];
