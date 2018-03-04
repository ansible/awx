export default ['$q', 'Rest', 'ProcessErrors', '$rootScope', 'Wait', 'DjangoSearchModel', 'SmartSearchService',
    function($q, Rest, ProcessErrors, $rootScope, Wait, DjangoSearchModel, SmartSearchService) {
        return {
            // kick off building a model for a specific endpoint
            // this is usually a list's basePath
            // unified_jobs is the exception, where we need to fetch many subclass OPTIONS and summary_fields
            initFieldset(path, name) {
                let defer = $q.defer();
                defer.resolve(this.getCommonModelOptions(path, name));
                return defer.promise;
            },

            getCommonModelOptions(path, name) {
                let resolve, base,
                    defer = $q.defer();

                this.url = path;
                resolve = this.options(path)
                    .then((res) => {
                        base = res.data.actions.GET;
                        let relatedSearchFields = res.data.related_search_fields;
                        defer.resolve({
                            models: {
                                [name]: new DjangoSearchModel(name, base, relatedSearchFields)
                            },
                            options: res
                        });
                    });
                return defer.promise;
            },

            replaceDefaultFlags (value) {
                value = value.toString().replace(/__icontains_DEFAULT/g, "__icontains");
                value = value.toString().replace(/__search_DEFAULT/g, "__search");

                return value;
            },

            replaceEncodedTokens(value) {
                return decodeURIComponent(value).replace(/"|'/g, "");
            },

            encodeTerms (values, key) {
                key = this.replaceDefaultFlags(key);

                if (!Array.isArray(values)) {
                    values = [values];
                }

                return values
                    .map(value => {
                        value = this.replaceDefaultFlags(value);
                        value = this.replaceEncodedTokens(value);
                        return [key, value]
                    })

            },
            // encodes ui-router params from {operand__key__comparator: value} pairs to API-consumable URL
            encodeQueryset(params) {
                if (typeof params !== 'object') {
                    return '';
                }

                return _.reduce(params, (result, value, key) => {
                    if (result !== '?') {
                        result += '&';
                    }

                    const encodedTermString = this.encodeTerms(value, key)
                        .map(([key, value]) => `${key}=${value}`)
                        .join('&');

                    return result += encodedTermString;
                }, '?');
            },
            // like encodeQueryset, but return an actual unstringified API-consumable http param object
            encodeQuerysetObject(params) {
                return _.reduce(params, (obj, value, key) => {
                    const encodedTerms = this.encodeTerms(value, key);

                    for (let encodedIndex in encodedTerms) {
                        const [encodedKey, encodedValue] = encodedTerms[encodedIndex];
                        obj[encodedKey] = obj[encodedKey] || [];
                        obj[encodedKey].push(encodedValue)
                    }

                    return obj;
                }, {});
            },
            // encodes a ui smart-search param to a django-friendly param
            // operand:key:comparator:value => {operand__key__comparator: value}
            encodeParam({ term, relatedSearchTerm, searchTerm, singleSearchParam }){
                // Assumption here is that we have a key and a value so the length
                // of the paramParts array will be 2.  [0] is the key and [1] the value
                let paramParts = SmartSearchService.splitTermIntoParts(term);
                let keySplit = paramParts[0].split('.');
                let exclude = false;
                let lessThanGreaterThan = paramParts[1].match(/^(>|<).*$/) ? true : false;
                if(keySplit[0].match(/^-/g)) {
                    exclude = true;
                    keySplit[0] = keySplit[0].replace(/^-/, '');
                }
                let paramString = exclude ? "not__" : "";
                let valueString = paramParts[1];
                if(keySplit.length === 1) {
                    if(searchTerm && !lessThanGreaterThan) {
                        if(singleSearchParam) {
                            paramString += keySplit[0] + '__icontains';
                        }
                        else {
                            paramString += keySplit[0] + '__icontains_DEFAULT';
                        }
                    }
                    else if(relatedSearchTerm) {
                        if(singleSearchParam) {
                            paramString += keySplit[0];
                        }
                        else {
                            paramString += keySplit[0] + '__search_DEFAULT';
                        }
                    }
                    else {
                        paramString += keySplit[0];
                    }
                }
                else {
                    paramString += keySplit.join('__');
                }

                if(lessThanGreaterThan) {
                    if(paramParts[1].match(/^>=.*$/)) {
                        paramString += '__gte';
                        valueString = valueString.replace(/^(>=)/,"");
                    }
                    else if(paramParts[1].match(/^<=.*$/)) {
                        paramString += '__lte';
                        valueString = valueString.replace(/^(<=)/,"");
                    }
                    else if(paramParts[1].match(/^<.*$/)) {
                        paramString += '__lt';
                        valueString = valueString.replace(/^(<)/,"");
                    }
                    else if(paramParts[1].match(/^>.*$/)) {
                        paramString += '__gt';
                        valueString = valueString.replace(/^(>)/,"");
                    }
                }

                if(singleSearchParam) {
                    return {[singleSearchParam]: paramString + "=" + valueString};
                }
                else {
                    return {[paramString] : encodeURIComponent(valueString)};
                }
            },
            // decodes a django queryset param into a ui smart-search tag or set of tags
            decodeParam(value, key){

                let decodeParamString = function(searchString) {
                    if(key === 'search') {
                        // Don't include 'search:' in the search tag
                        return decodeURIComponent(`${searchString}`);
                    }
                    else {
                        key = key.toString().replace(/__icontains_DEFAULT/g, "");
                        key = key.toString().replace(/__search_DEFAULT/g, "");
                        let split = key.split('__');
                        let decodedParam = searchString;
                        let exclude = false;
                        if(key.startsWith('not__')) {
                            exclude = true;
                            split = split.splice(1, split.length);
                        }
                        if(key.endsWith('__gt')) {
                            decodedParam = '>' + decodedParam;
                            split = split.splice(0, split.length-1);
                        }
                        else if(key.endsWith('__lt')) {
                            decodedParam = '<' + decodedParam;
                            split = split.splice(0, split.length-1);
                        }
                        else if(key.endsWith('__gte')) {
                            decodedParam = '>=' + decodedParam;
                            split = split.splice(0, split.length-1);
                        }
                        else if(key.endsWith('__lte')) {
                            decodedParam = '<=' + decodedParam;
                            split = split.splice(0, split.length-1);
                        }

                        let uriDecodedParam = decodeURIComponent(decodedParam);

                        return exclude ? `-${split.join('.')}:${uriDecodedParam}` : `${split.join('.')}:${uriDecodedParam}`;
                    }
                };

                if (Array.isArray(value)){
                    value = _.uniq(_.flattenDeep(value));
                    return _.map(value, (item) => {
                        return decodeParamString(item);
                    });
                }
                else {
                    return decodeParamString(value);
                }
            },
            convertToSearchTags(obj) {
                const tags = [];
                for (let key in obj) {
                    const value = obj[key];
                    tags.push(this.decodeParam(value, key));
                }
                return tags;
            },
            // encodes a django queryset for ui-router's URLMatcherFactory
            // {operand__key__comparator: value, } => 'operand:key:comparator:value;...'
            // value.isArray expands to:
            // {operand__key__comparator: [value1, value2], } => 'operand:key:comparator:value1;operand:key:comparator:value1...'
            encodeArr(params) {
                let url;
                url = _.reduce(params, (result, value, key) => {
                    return result.concat(encodeUrlString(value, key));
                }, []);

                return url.join(';');

                // {key:'value'} => 'key:value'
                // {key: [value1, value2, ...]} => ['key:value1', 'key:value2']
                function encodeUrlString(value, key){
                    if (Array.isArray(value)){
                        value = _.uniq(_.flattenDeep(value));
                        return _.map(value, (item) => {
                            return `${key}:${item}`;
                        });
                    }
                    else {
                        return `${key}:${value}`;
                    }
                }
            },

            // decodes a django queryset for ui-router's URLMatcherFactory
            // 'operand:key:comparator:value,...' => {operand__key__comparator: value, }
            decodeArr(arr) {
                let params = {};
                _.forEach(arr.split(';'), (item) => {
                    let key = item.split(':')[0],
                        value = item.split(':')[1];
                    if(!params[key]){
                        params[key] = value;
                    }
                    else if (Array.isArray(params[key])){
                        params[key] = _.uniq(_.flattenDeep(params[key]));
                        params[key].push(value);
                    }
                    else {
                        params[key] = [params[key], value];
                    }
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
                    .then(function(response) {
                        Wait('stop');

                        if (response
                            .headers('X-UI-Max-Events') !== null) {
                            response.data.maxEvents = response.
                                headers('X-UI-Max-Events');
                        }

                        return response;
                    })
                    .catch(function(response) {
                        Wait('stop');

                        this.error(response.data, response.status);

                        throw response;
                    }.bind(this));
            },
            error(data, status) {
                if(data && data.detail){
                    let error = typeof data.detail === "string" ? data.detail : JSON.parse(data.detail);

                    if(_.isArray(error)){
                        data.detail = error[0];
                    }
                }
                ProcessErrors($rootScope, data, status, null, {
                    hdr: 'Error!',
                    msg: `Invalid search term entered. GET returned: ${status}`
                });
            },
            // Removes state definition defaults and pagination terms
            stripDefaultParams(params, defaults) {
                if(defaults) {
                    let stripped =_.pick(params, (value, key) => {
                        // setting the default value of a term to null in a state definition is a very explicit way to ensure it will NEVER generate a search tag, even with a non-default value
                        return defaults[key] !== value && key !== 'order_by' && key !== 'page' && key !== 'page_size' && defaults[key] !== null;
                    });
                    let strippedCopy = _.cloneDeep(stripped);
                    if(_.keys(_.pick(defaults, _.keys(strippedCopy))).length > 0){
                        for (var key in strippedCopy) {
                            if (strippedCopy.hasOwnProperty(key)) {
                                let value = strippedCopy[key];
                                if(_.isArray(value)){
                                    let index = _.indexOf(value, defaults[key]);
                                    value = value.splice(index, 1)[0];
                                }
                            }
                        }
                        stripped = strippedCopy;
                    }
                    return _(strippedCopy).map(this.decodeParam).flatten().value();
                }
                else {
                    return _(params).map(this.decodeParam).flatten().value();
                }
            }
        };
    }
];
