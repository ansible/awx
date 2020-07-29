export default
['$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait', function($rootScope, Rest, GetBasePath, ProcessErrors, Wait){
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
        error: function(data) {
            ProcessErrors($rootScope, data.data, data.status, null, { hdr: 'Error!',
            msg: 'Call to ' + this.url + '. GET returned: ' + data.status });
        },
        success: function(data){
            return data;
        },
        // HTTP methods
        get: function(params){
            Wait('start');
            this.url = GetBasePath('inventory_sources') + '?' + this.stringifyParams(params);
            Rest.setUrl(this.url);
            return Rest.get()
                .then(this.success.bind(this))
                .catch(this.error.bind(this))
                .finally(Wait('stop'));
        },
        post: function(inventory_source){
            Wait('start');
            this.url = GetBasePath('inventory_sources');
            Rest.setUrl(this.url);
            return Rest.post(inventory_source)
                .then(this.success.bind(this))
                .catch(this.error.bind(this))
                .finally(Wait('stop'));
        },
        put: function(inventory_source){
            Wait('start');
            this.url = GetBasePath('inventory_sources') + inventory_source.id;
            Rest.setUrl(this.url);
            return Rest.put(inventory_source)
                .then(this.success.bind(this))
                .catch(this.error.bind(this))
                .finally(Wait('stop'));
        },
        delete: function(id){
            Wait('start');
            this.url = GetBasePath('inventory_sources') + id;
            Rest.setUrl(this.url);
            return Rest.destroy()
                .then(this.success.bind(this))
                .catch(this.error.bind(this))
                .finally(Wait('stop'));
        },
        options: function(){
            this.url = GetBasePath('inventory_sources');
            Rest.setUrl(this.url);
            return Rest.options()
                .then(this.success.bind(this))
                .catch(this.error.bind(this));
        },
        getCredential: function(id){
            Wait('start');
            this.url = GetBasePath('credentials') + id;
            Rest.setUrl(this.url);
            return Rest.get()
                .then(this.success.bind(this))
                .catch(this.error.bind(this))
                .finally(Wait('stop'));
        },
        getInventorySource: function(params){
            Wait('start');
            this.url = GetBasePath('inventory_sources') + '?' + this.stringifyParams(params);
            Rest.setUrl(this.url);
            return Rest.get()
                .then(this.success.bind(this))
                .catch(this.error.bind(this))
                .finally(Wait('stop'));
        },
        putInventorySource: function(params, url){
            Wait('start');
            this.url = url;
            Rest.setUrl(this.url);
            return Rest.put(params)
                .then(this.success.bind(this))
                .catch(this.error.bind(this))
                .finally(Wait('stop'));
        },
        // these relationship setters could be consolidated, but verbosity makes the operation feel more clear @ controller level
        associateGroup: function(group, target){
            Wait('start');
            this.url = GetBasePath('groups') + target + '/children/';
            Rest.setUrl(this.url);
            return Rest.post(group)
                .then(this.success.bind(this))
                .catch(this.error.bind(this))
                .finally(Wait('stop'));
        },
        disassociateGroup: function(group, parent){
            Wait('start');
            this.url = GetBasePath('groups') + parent + '/children/';
            Rest.setUrl(this.url);
            return Rest.post({id: group, disassociate: 1})
                .then(this.success.bind(this))
                .catch(this.error.bind(this))
                .finally(Wait('stop'));
        },
        promote: function(group, inventory){
            Wait('start');
            this.url = GetBasePath('inventory') + inventory + '/groups/';
            Rest.setUrl(this.url);
            return Rest.post({id: group, disassociate: 1})
                .then(this.success.bind(this))
                .catch(this.error.bind(this))
                .finally(Wait('stop'));
        },
        deleteHosts(id) {
            this.url = GetBasePath('inventory_sources') + id + '/hosts/';
            Rest.setUrl(this.url);
            return Rest.destroy()
                .then(this.success.bind(this))
                .catch(this.error.bind(this))
                .finally();
        },
        deleteGroups(id) {
            this.url = GetBasePath('inventory_sources') + id + '/groups/';
            Rest.setUrl(this.url);
            return Rest.destroy()
                .then(this.success.bind(this))
                .catch(this.error.bind(this))
                .finally();
        }
    };
}];
