function searchWithoutKey (term, singleSearchParam = null) {
    if (singleSearchParam) {
        return { [singleSearchParam]: `search=${encodeURIComponent(term)}` };
    }
    return { search: encodeURIComponent(term) };
}

function QuerysetService ($q, Rest, ProcessErrors, $rootScope, Wait, DjangoSearchModel, SmartSearchService) {
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
            let base,
                defer = $q.defer();

            this.url = path;
            this.options(path)
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
            if (value) {
                value = value.toString().replace(/__icontains_DEFAULT/g, "__icontains");
                value = value.toString().replace(/__search_DEFAULT/g, "__search");
            }

            return value;
        },
        replaceEncodedTokens(value) {
            return decodeURIComponent(value).replace(/"|'/g, "");
        },
        encodeTerms(value, key, singleSearchParam){
            key = this.replaceDefaultFlags(key);
            value = this.replaceDefaultFlags(value);
            var that = this;
            if (Array.isArray(value)){
                value = _.uniq(_.flattenDeep(value));
                let concated = '';
                angular.forEach(value, function(item){
                    if(item && typeof item === 'string' && !singleSearchParam) {
                        item = that.replaceEncodedTokens(item);
                    }
                    concated += `${key}=${item}&`;
                });

                return concated;
            }
            else {
                if(value && typeof value === 'string' && !singleSearchParam) {
                    value = this.replaceEncodedTokens(value);
                }

                return `${key}=${value}&`;
            }
        },
        // encodes ui-router params from {operand__key__comparator: value} pairs to API-consumable URL
        encodeQueryset(params, singleSearchParam) {
            let queryset;
            queryset = _.reduce(params, (result, value, key) => {
                return result + this.encodeTerms(value, key, singleSearchParam);
            }, '');
            queryset = queryset.substring(0, queryset.length - 1);
            return angular.isObject(params) ? `?${queryset}` : '';

        },
        // like encodeQueryset, but return an actual unstringified API-consumable http param object
        encodeQuerysetObject(params) {
            return _.reduce(params, (obj, value, key) => {
                const encodedKey = this.replaceDefaultFlags(key);
                const values = Array.isArray(value) ? value : [value];

                obj[encodedKey] = values
                    .map(value => this.replaceDefaultFlags(value))
                    .map(value => this.replaceEncodedTokens(value))
                    .join(',');

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

            if (!arr) {
                return params;
            }

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
        search(endpoint, params, singleSearchParam) {
            Wait('start');
            this.url = `${endpoint}${this.encodeQueryset(params, singleSearchParam)}`;
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
        stripDefaultParams(params, defaultParams) {
            if (!params) {
                return [];
            }
            if(defaultParams) {
                let stripped =_.pickBy(params, (value, key) => {
                    // setting the default value of a term to null in a state definition is a very explicit way to ensure it will NEVER generate a search tag, even with a non-default value
                    return defaultParams[key] !== value && key !== 'order_by' && key !== 'page' && key !== 'page_size' && defaultParams[key] !== null;
                });
                let strippedCopy = _.cloneDeep(stripped);
                if(_.keys(_.pickBy(defaultParams, _.keys(strippedCopy))).length > 0){
                    for (var key in strippedCopy) {
                        if (strippedCopy.hasOwnProperty(key)) {
                            let value = strippedCopy[key];
                            if(_.isArray(value)){
                                let index = _.indexOf(value, defaultParams[key]);
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
        },
        mergeQueryset (queryset, additional, singleSearchParam) {
            const space = '%20and%20';

            const merged = _.mergeWith({}, queryset, additional, (objectValue, sourceValue, key, object) => {
                if (!(object[key] && object[key] !== sourceValue)) {
                    // // https://lodash.com/docs/3.10.1#each
                    // If this returns undefined merging is handled by default _.merge algorithm
                    return undefined;
                }

                if (_.isArray(object[key])) {
                    object[key].push(sourceValue);
                    return object[key];
                }

                if (singleSearchParam) {
                    if (!object[key]) {
                        return sourceValue;
                    }

                    const singleSearchParamKeys = object[key].split(space);

                    if (_.includes(singleSearchParamKeys, sourceValue)) {
                        return object[key];
                    }

                    return `${object[key]}${space}${sourceValue}`;
                }

                // Start the array of keys
                return [object[key], sourceValue];
            });

            return merged;
        },
        getSearchInputQueryset (searchInput, isFilterableBaseField = null, isRelatedField = null, isAnsibleFactField = null, singleSearchParam = null) {
            // XXX Should find a better approach than passing in the two 'is...Field' callbacks XXX
            const encodedAnd = '%20and%20';
            const encodedOr = '%20or%20';
            let params = {};

            // Remove leading/trailing whitespace if there is any
            const terms = (searchInput) ? searchInput.trim() : '';

            if (!(terms && terms !== '')) {
                return;
            }

            let splitTerms;

            if (singleSearchParam === 'host_filter') {
                splitTerms = SmartSearchService.splitFilterIntoTerms(terms);
            } else {
                splitTerms = SmartSearchService.splitSearchIntoTerms(terms);
            }

            const combineSameSearches = (a, b) => {
                if (!a) {
                    return undefined;
                }

                if (_.isArray(a)) {
                    return a.concat(b);
                }

                if (singleSearchParam) {
                    if (b === 'or') {
                        return `${a}${encodedOr}`;
                    } else if (a.match(/%20or%20$/g)) {
                        return `${a}${b}`;
                    } else {
                        return `${a}${encodedAnd}${b}`;
                    }
                }

                return [a, b];
            };

            _.each(splitTerms, term => {
                const termParts = SmartSearchService.splitTermIntoParts(term);
                let termParams;

                if (termParts.length === 1) {
                    if (singleSearchParam && termParts[0].toLowerCase() === "or") {
                        termParams = { [singleSearchParam]: "or" };
                    } else {
                        termParams = searchWithoutKey(term, singleSearchParam);
                    }
                } else if ((isAnsibleFactField && isAnsibleFactField(termParts)) || (isFilterableBaseField && isFilterableBaseField(termParts))) {
                    termParams = this.encodeParam({ term, singleSearchParam, searchTerm: true });
                } else if (isRelatedField && isRelatedField(termParts)) {
                    termParams = this.encodeParam({ term, singleSearchParam, relatedSearchTerm: true });
                } else {
                    termParams = searchWithoutKey(term, singleSearchParam);
                }

                params = _.mergeWith(params, termParams, combineSameSearches);
            });

            return params;
        },
        removeTermsFromQueryset(queryset, term, isFilterableBaseField, isRelatedField = null, isAnsibleFactField = null, singleSearchParam = null) {
            const modifiedQueryset = _.cloneDeep(queryset);

            const removeSingleTermFromQueryset = (value, key) => {
                const space = '%20and%20';

                if (Array.isArray(modifiedQueryset[key])) {
                    modifiedQueryset[key] = modifiedQueryset[key].filter(item => item !== value);
                    if (modifiedQueryset[key].length < 1) {
                        delete modifiedQueryset[key];
                    }
                } else if (singleSearchParam && _.get(modifiedQueryset, singleSearchParam, []).includes(space)) {
                    const searchParamParts = modifiedQueryset[singleSearchParam].split(space);
                    // The value side of each paramPart might have been encoded in
                    // SmartSearch.splitFilterIntoTerms
                    _.each(searchParamParts, (paramPart, paramPartIndex) => {
                        searchParamParts[paramPartIndex] = decodeURIComponent(paramPart);
                    });

                    const paramPartIndex = searchParamParts.indexOf(decodeURIComponent(value));

                    if (paramPartIndex !== -1) {
                        searchParamParts.splice(paramPartIndex, 1);
                    }

                    modifiedQueryset[singleSearchParam] = searchParamParts.join(space);

                } else {
                    delete modifiedQueryset[key];
                }
            };

            const termParts = SmartSearchService.splitTermIntoParts(term);

            let removed;

            if (termParts.length === 1) {
                removed = searchWithoutKey(term, singleSearchParam);
            } else if ((isAnsibleFactField && isAnsibleFactField(termParts)) || (isFilterableBaseField && isFilterableBaseField(termParts))) {
                removed = this.encodeParam({ term, singleSearchParam, searchTerm: true });
            } else if (isRelatedField && isRelatedField(termParts)) {
                removed = this.encodeParam({ term, singleSearchParam, relatedSearchTerm: true });
            } else {
                removed = searchWithoutKey(term, singleSearchParam);
            }

            if (!removed) {
                removed = searchWithoutKey(termParts[termParts.length - 1], singleSearchParam);
            }

            _.each(removed, removeSingleTermFromQueryset);

            return modifiedQueryset;
        },
        createSearchTagsFromQueryset(queryset, defaultParams = null, singleSearchParam = null) {
            const space = '%20and%20';
            const modifiedQueryset = angular.copy(queryset);

            let searchTags = [];

            if (singleSearchParam && modifiedQueryset[singleSearchParam]) {
                const searchParam = modifiedQueryset[singleSearchParam].split(space);
                delete modifiedQueryset[singleSearchParam];

                $.each(searchParam, (index, param) => {
                    const paramParts = decodeURIComponent(param).split(/=(.+)/);
                    const reconstructedSearchString = this.decodeParam(paramParts[1], paramParts[0]);

                    searchTags.push(reconstructedSearchString);
                });
            }

            return searchTags.concat(this.stripDefaultParams(modifiedQueryset, defaultParams));
        }
    };
}

QuerysetService.$inject = [
    '$q',
    'Rest',
    'ProcessErrors',
    '$rootScope',
    'Wait',
    'DjangoSearchModel',
    'SmartSearchService',
];

export default QuerysetService;
