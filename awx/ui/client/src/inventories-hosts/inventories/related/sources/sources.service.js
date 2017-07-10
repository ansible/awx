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
                this.url = GetBasePath('inventory_sources') + '?' + this.stringifyParams(params);
                Rest.setUrl(this.url);
                return Rest.get()
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            post: function(inventory_source){
                Wait('start');
                this.url = GetBasePath('inventory_sources');
                Rest.setUrl(this.url);
                return Rest.post(inventory_source)
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            put: function(inventory_source){
                Wait('start');
                this.url = GetBasePath('inventory_sources') + inventory_source.id;
                Rest.setUrl(this.url);
                return Rest.put(inventory_source)
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            delete: function(id){
                Wait('start');
                this.url = GetBasePath('inventory_sources') + id;
                Rest.setUrl(this.url);
                return Rest.destroy()
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            options: function(){
                this.url = GetBasePath('inventory_sources');
                Rest.setUrl(this.url);
                return Rest.options()
                    .success(this.success.bind(this))
                    .error(this.error.bind(this));
            },
            getCredential: function(id){
                Wait('start');
                this.url = GetBasePath('credentials') + id;
                Rest.setUrl(this.url);
                return Rest.get()
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            getInventorySource: function(params){
                Wait('start');
                this.url = GetBasePath('inventory_sources') + '?' + this.stringifyParams(params);
                Rest.setUrl(this.url);
                return Rest.get()
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            putInventorySource: function(params, url){
                Wait('start');
                this.url = url;
                Rest.setUrl(this.url);
                return Rest.put(params)
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            // these relationship setters could be consolidated, but verbosity makes the operation feel more clear @ controller level
            associateGroup: function(group, target){
                Wait('start');
                this.url = GetBasePath('groups') + target + '/children/';
                Rest.setUrl(this.url);
                return Rest.post(group)
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            disassociateGroup: function(group, parent){
                Wait('start');
                this.url = GetBasePath('groups') + parent + '/children/';
                Rest.setUrl(this.url);
                return Rest.post({id: group, disassociate: 1})
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            promote: function(group, inventory){
                Wait('start');
                this.url = GetBasePath('inventory') + inventory + '/groups/';
                Rest.setUrl(this.url);
                return Rest.post({id: group, disassociate: 1})
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            encodeGroupBy(source, group_by){
                source = source && source.value ? source.value : '';
                if(source === 'ec2'){
                    return _.map(group_by, 'value').join(',');
                }
                if(source === 'vmware'){
                    group_by = _.map(group_by, (i) => {return i.value;});
                    $("#inventory_source_group_by").siblings(".select2").first().find(".select2-selection__choice").each(function(optionIndex, option){
                        group_by.push(option.title);
                    });
                    group_by = (Array.isArray(group_by)) ?  _.uniq(group_by).join() : "";
                    return group_by;
                }
                else {
                    return;
                }
            }
        };
    }];
