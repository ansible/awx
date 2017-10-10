let $http;
let $q;
let cache;

function request (method, resource) {
    if (Array.isArray(method)) {
        let promises = method.map((_method_, i) => {
            return this.request(_method_, Array.isArray(resource) ? resource[i] : resource);
        });

        return $q.all(promises);
    }

    if (this.isCacheable(method, resource)) {
        return this.requestWithCache(method, resource);
    }
 
    return this.http[method](resource);
}

function requestWithCache (method, resource) {
    let key = cache.createKey(method, this.path, resource);

    return cache.get(key)
        .then(data => {
            if (data) {
                this.model[method.toUpperCase()] = data;

                return data;
            }

            return this.http[method](resource)
                .then(res => {
                    cache.put(key, res.data);

                    return res;
                });
        });
}

/**
 * Intended to be useful in searching and filtering results using params
 * supported by the API.
 *
 * @arg {Object} params - An object of keys and values to to format and
 * to the URL as a query string. Refer to the API documentation for the
 * resource in use for specifics.
 * @arg {Object} config - Configuration specific to the UI to accommodate
 * common use cases.
 *
 * @yields {boolean} - Indicating a match has been found. If so, the results
 * are set on the model.
 */
function search (params = {}, config = {}) {
    let req = {
        method: 'GET',
        url: this.path
    };

    if (typeof params === 'string') {
        req.url = `?params`;
    } else if (Array.isArray(params)) {
        req.url += `?${params.join('&')}`;
    } else {
        req.params = params;
    }

    return $http(req)
        .then(({ data }) => {
            if (!data.count) {
                return false;
            }

            if (config.unique) {
                if (data.count !== 1) {
                    return false;
                }

                this.model.GET = data.results[0];
            } else {
                this.model.GET = data;
            }

            return true;
        });
}

function httpGet (resource) {
    let req = {
        method: 'GET',
        url: this.path
    };

    if (typeof resource === 'object') {
        this.model.GET = resource;

        return $q.resolve();
    } else if (resource) {
        req.url = `${this.path}${resource}/`;
    }

    return $http(req)
        .then(res => {
            this.model.GET = res.data;

            return res;
        });
}

function httpPost (data) {
    let req = {
        method: 'POST',
        url: this.path,
        data
    };

    return $http(req).then(res => {
        this.model.GET = res.data;

        return res;
    });
}

function httpPut (changes) {
    let model = Object.assign(this.get(), changes);

    let req = {
        method: 'PUT',
        url: `${this.path}${model.id}/`,
        data: model
    };

    return $http(req).then(res => res);
}

function httpOptions (resource) {
    let req = {
        method: 'OPTIONS',
        url: this.path
    };

    if (resource) {
        req.url = `${this.path}${resource}/`;
    }

    return $http(req)
        .then(res => {
            this.model.OPTIONS = res.data;

            return res;
        });
}

function options (keys) {
    return this.find('options', keys);
}

function get (keys) {
    return this.find('get', keys);
}

function unset (method, keys) {
    if (!keys) {
        keys = method;
        method = 'GET';
    }
    
    method = method.toUpperCase();
    keys = keys.split('.');

    if (!keys.length) {
        delete this.model[method];
    } else if (keys.length === 1) {
        delete this.model[method][keys[0]];
    } else {
        let property = keys.splice(-1);
        keys = keys.join('.');

        let model = this.find(method, keys)
        delete model[property];
    }
}

function set (method, keys, value) {
    if (!value) {
        value = keys;
        keys = method;
        method = 'GET';
    }
    
    keys = keys.split('.');

    if (keys.length === 1) {
        model[keys[0]] = value;
    } else {
        let property = keys.splice(-1);
        keys = keys.join('.');

        let model = this.find(method, keys)

        model[property] = value;
    }
}

function match (method, key, value) {
    if(!value) {
        value = key;
        key = method;
        method = 'GET';
    }

    let model = this.model[method.toUpperCase()];

    if (!model) {
        return null;
    }

    if (!model.results) {
        if (model[key] === value) {
            return model;
        }

        return null;
    }

    let result = model.results.filter(result => result[key] === value);

    return result.length === 0 ? null : result[0];
}

function find (method, keys) {
    let value = this.model[method.toUpperCase()];

    if (!keys) {
        return value;
    }

    try {
        keys = keys.split('.');

        keys.forEach(key => {
            let bracketIndex = key.indexOf('[');
            let hasArray = bracketIndex !== -1;

            if (!hasArray) {
                value = value[key];
                return;
            }

            if (bracketIndex === 0) {
                value = value[Number(key.substring(1, key.length - 1))];
                return;
            }

            let prop = key.substring(0, bracketIndex);
            let index = Number(key.substring(bracketIndex + 1, key.length - 1));

            value = value[prop][index];
        });
    } catch (err) {
        return undefined;
    }

    return value;
}

function has (method, keys) {
    if (!keys) {
        keys = method;
        method = 'GET';
    }

    method = method.toUpperCase();

    let value;
    switch (method) {
        case 'OPTIONS':
            value = this.options(keys);
            break;
        default:
            value = this.get(keys);
    }

    return value !== undefined && value !== null;
}

function extend (method, related) {
    if (!related) {
        related = method
        method = 'GET'
    } else {
        method = method.toUpperCase()
    }

    if (this.has(method, `related.${related}`)) {
        let id = this.get('id')

        let req = {
            method,
            url: this.get(`related.${related}`)
        };

        return $http(req)
            .then(({data}) => {
                this.set(method, `related.${related}`, data);
                return this;
            })
    }

    return Promise.reject(new Error(`No related property, ${related}, exists`));
}

function normalizePath (resource) {
    let version = '/api/v2/';

    return `${version}${resource}/`;
}

function isEditable () {
    let canEdit = this.get('summary_fields.user_capabilities.edit');

    if (canEdit) {
        return true;
    }

    if (this.has('options', 'actions.PUT')) {
        return true;
    }

    return false;

}

function isCreatable () {
    if (this.has('options', 'actions.POST')) {
        return true;
    }

    return false;
}

function isCacheable () {
    if (this.settings.cache === true) {
        return true;
    }

    return false;
}

function graft (id) {
    let item = this.get('results').filter(result => result.id === id);

    item = item ? item[0] : undefined;

    if (!item) {
        return undefined;
    }

    return new this.Constructor('get', item, true);
}

/**
 * `create` is called on instantiation of every model. Models can be
 * instantiated empty or with `GET` and/or `OPTIONS` requests that yield data.
 * If model data already exists a new instance can be created (see: `graft`)
 * with existing data.
 *
 * @arg {string=} method - Populate the model with `GET` or `OPTIONS` data.
 * @arg {(string|Object)=} resource - An `id` reference to a particular
 * resource or an existing model's data.
 * @arg {boolean=} graft - Create a new instance from existing model data.
 *
 * @returns {(Object|Promise)} - Returns a reference to the model instance
 * if an empty instance or graft is created. Otherwise, a promise yielding
 * a model instance is returned.
 */
function create (method, resource, graft, config) {
    if (!method) {
        return this;
    }

    this.promise = this.request(method, resource, config);

    if (graft) {
        return this;
    }

    return this.promise
        .then(() => this);
}

/**
 * Base functionality for API interaction.
 *
 * @arg {string} path - The API resource for the model extending BaseModel to
 * use.
 * @arg {Object=} settings - Configuration applied to all instances of the
 * extending model.
 * @arg {boolean=} settings.cache - Cache the model data.
 *
 */
function BaseModel (path, settings) {
    this.create = create;
    this.find = find;
    this.get = get;
    this.graft = graft;
    this.has = has;
    this.isEditable = isEditable;
    this.isCacheable = isCacheable;
    this.isCreatable = isCreatable;
    this.match = match;
    this.normalizePath = normalizePath;
    this.options = options;
    this.request = request;
    this.requestWithCache = requestWithCache;
    this.search = search;
    this.set = set;
    this.unset = unset;
    this.extend = extend;

    this.http = {
        get: httpGet.bind(this),
        options: httpOptions.bind(this),
        post: httpPost.bind(this),
        put: httpPut.bind(this),
    };

    this.model = {};
    this.path = this.normalizePath(path);
    this.settings = settings || {};
};

function BaseModelLoader (_$http_, _$q_, _cache_) {
    $http = _$http_;
    $q = _$q_;
    cache = _cache_;

    return BaseModel;
}

BaseModelLoader.$inject = ['$http', '$q', 'CacheService'];

export default BaseModelLoader;
