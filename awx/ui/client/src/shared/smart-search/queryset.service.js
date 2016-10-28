export default ['$q', 'Rest', 'ProcessErrors', '$rootScope', 'Wait', 'DjangoSearchModel', '$cacheFactory', 'GetBasePath',
    function($q, Rest, ProcessErrors, $rootScope, Wait, DjangoSearchModel, $cacheFactory, GetBasePath) {
        return {
            // kick off building a model for a specific endpoint
            // this is usually a list's basePath
            // unified_jobs is the exception, where we need to fetch many subclass OPTIONS and summary_fields
            initFieldset(path, name, relations) {
                // get or set $cachFactory.Cache object with id '$http'
                let defer = $q.defer(),
                    cache = $cacheFactory.get('$http') || $cacheFactory('$http');
                defer.resolve(this.getCommonModelOptions(path, name, relations, cache));
                return defer.promise;
            },

            getCommonModelOptions(path, name, relations, cache) {
                let resolve, base,
                    defer = $q.defer();

                // grab a single model from the cache, if present
                if (cache.get(path)) {
                    defer.resolve({[name] : new DjangoSearchModel(name, path, cache.get(path), relations)});
                } else {
                    this.url = path;
                    resolve = this.options(path)
                        .then((res) => {
                            base = res.data.actions.GET;
                            defer.resolve({[name]: new DjangoSearchModel(name, path, base, relations)});
                        });
                }
                return defer.promise;
            },

            /* @extendme
            // example:
            // retrieving options from a polymorphic model (unified_job)
            getPolymorphicModelOptions(path, name) {
                let defer = $q.defer(),
                    paths = {
                        project_update: GetBasePath('project_update'),
                        inventory_update: GetBasePath('inventory_update'),
                        job: GetBasePath('jobs'),
                        ad_hoc_command: GetBasePath('ad_hoc_commands'),
                        system_job: GetBasePath('system_jobs')
                    };
                defer.all( // for each getCommonModelOptions() );
                return defer.promise;
            },
            */

            // encodes ui-router params from {operand__key__comparator: value} pairs to API-consumable URL
            encodeQueryset(params) {
                let queryset;
                queryset = _.reduce(params, (result, value, key) => {
                    return result + `${key}=${value}&`;
                }, '');
                queryset = queryset.substring(0, queryset.length - 1);
                return angular.isObject(params) ? `?${queryset}` : '';
            },
            // encodes a ui smart-search param to a django-friendly param
            // operand:key:comparator:value => {operand__key__comparator: value}
            encodeParam(param){
                let split = param.split(':');
                return {[split.slice(0,split.length -1).join('__')] : split[split.length-1]};
            },
            // decodes a django queryset param into ui smart-search param
            decodeParam(key, value){
                return `${key.split('__').join(':')}:${value}`;
            },

            // encodes a django queryset for ui-router's URLMatcherFactory
            // {operand__key__comparator: value, } => 'operand:key:comparator:value,...'
            encodeArr(params) {
                let url;
                url = _.reduce(params, (result, value, key) => {
                    return result.concat(`${key}:${value}`);
                }, []);
                return url.join(';');
            },

            // decodes a django queryset for ui-router's URLMatcherFactory
            // 'operand:key:comparator:value,...' => {operand__key__comparator: value, }
            decodeArr(arr) {
                let params = {};
                _.forEach(arr.split(';'), (item) => {
                    let key = item.split(':')[0],
                        value = item.split(':')[1];
                    params[key] = value;
                });
                return params;
            },
            // REST utilities
            options(endpoint) {
                Rest.setUrl(endpoint);
                return Rest.options(endpoint);
            },
            search(endpoint, params) {
                Wait('start');
                this.url = `${endpoint}${this.encodeQueryset(params)}`;
                Rest.setUrl(this.url);
                return Rest.get()
                    .success(this.success.bind(this))
                    .error(this.error.bind(this))
                    .finally(Wait('stop'));
            },
            error(data, status) {
                ProcessErrors($rootScope, data, status, null, {
                    hdr: 'Error!',
                    msg: 'Call to ' + this.url + '. GET returned: ' + status
                });
            },
            success(data) {
                return data;
            },
        };
    }
];
