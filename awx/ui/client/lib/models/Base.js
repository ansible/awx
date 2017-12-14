let $http;
let $q;
let cache;
let strings;

function request (method, resource, config) {
    let req = this.parseRequestConfig(method, resource, config);

    if (Array.isArray(req.method)) {
        const promises = req.method.map((_method, i) => {
            const _resource = Array.isArray(req.resource) ? req.resource[i] : req.resource;

            req = this.parseRequestConfig(_method, _resource, config);

            if (this.isCacheable(req)) {
                return this.requestWithCache(req);
            }

            return this.request(req);
        });

        return $q.all(promises);
    }

    if (this.isCacheable(req)) {
        return this.requestWithCache(req);
    }

    return this.http[req.method](req);
}

function requestWithCache (config) {
    const key = cache.createKey(config.method, this.path, config.resource);

    return cache.get(key)
        .then(data => {
            if (data) {
                this.model[config.method.toUpperCase()] = data;

                return data;
            }

            return this.http[config.method](config)
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
    const req = {
        method: 'GET',
        url: this.path
    };

    if (typeof params === 'string') {
        req.url = '?params';
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

                [this.model.GET] = data.results;
            } else {
                this.model.GET = data;
            }

            return true;
        });
}

function httpGet (config = {}) {
    const req = {
        method: 'GET',
        url: this.path
    };

    if (config.params) {
        req.params = config.params;
    }

    if (typeof config.resource === 'object') {
        this.model.GET = config.resource;

        return $q.resolve();
    } else if (config.resource) {
        req.url = `${this.path}${config.resource}/`;
    }

    return $http(req)
        .then(res => {
            this.model.GET = res.data;

            return res;
        });
}

function httpPost (config = {}) {
    const req = {
        method: 'POST',
        url: this.path,
        data: config.data
    };

    return $http(req)
        .then(res => {
            this.model.GET = res.data;

            return res;
        });
}

function httpPatch (config = {}) {
    const req = {
        method: 'PUT',
        url: `${this.path}${this.get('id')}/`,
        data: config.changes
    };

    return $http(req);
}

function httpPut (config = {}) {
    const model = _.merge(this.get(), config.data);

    const req = {
        method: 'PUT',
        url: `${this.path}${this.get('id')}/`,
        data: model
    };

    return $http(req);
}

function httpOptions (config = {}) {
    const req = {
        method: 'OPTIONS',
        url: this.path
    };

    if (config.resource) {
        req.url = `${this.path}${config.resource}/`;
    }

    return $http(req)
        .then(res => {
            this.model.OPTIONS = res.data;

            return res;
        });
}

function httpDelete (config = {}) {
    const req = {
        method: 'DELETE',
        url: this.path
    };

    if (config.resource) {
        req.url = `${this.path}${config.resource}/`;
    }

    return $http(req);
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
        const property = keys.splice(-1);
        keys = keys.join('.');

        const model = this.find(method, keys);
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
        this.model[keys[0]] = value;
    } else {
        const property = keys.splice(-1);
        keys = keys.join('.');

        const model = this.find(method, keys);

        model[property] = value;
    }
}

function match (method, key, value) {
    if (!value) {
        value = key;
        key = method;
        method = 'GET';
    }

    const model = this.model[method.toUpperCase()];

    if (!model) {
        return null;
    }

    if (!model.results) {
        if (model[key] === value) {
            return model;
        }

        return null;
    }

    const result = model.results.filter(object => object[key] === value);

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
            const bracketIndex = key.indexOf('[');
            const hasArray = bracketIndex !== -1;

            if (!hasArray) {
                value = value[key];
                return;
            }

            if (bracketIndex === 0) {
                value = value[Number(key.substring(1, key.length - 1))];
                return;
            }

            const prop = key.substring(0, bracketIndex);
            const index = Number(key.substring(bracketIndex + 1, key.length - 1));

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
        related = method;
        method = 'GET';
    } else {
        method = method.toUpperCase();
    }

    if (this.has(method, `related.${related}`)) {
        const req = {
            method,
            url: this.get(`related.${related}`)
        };

        return $http(req)
            .then(({ data }) => {
                this.set(method, `related.${related}`, data);

                return this;
            });
    }

    return Promise.reject(new Error(`No related property, ${related}, exists`));
}

function normalizePath (resource) {
    const version = '/api/v2/';

    return `${version}${resource}/`;
}

function isEditable () {
    const canEdit = this.get('summary_fields.user_capabilities.edit');

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

function getDependentResourceCounts (id) {
    this.setDependentResources(id);

    const promises = [];

    this.dependentResources.forEach(resource => {
        promises.push(resource.model.request('get', { params: resource.params })
            .then(res => ({
                label: resource.model.label,
                count: res.data.count
            })));
    });

    return Promise.all(promises);
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
 * @arg {config=} config - Create a new instance from existing model data.
 *
 * @returns {(Object|Promise)} - Returns a reference to the model instance
 * if an empty instance or graft is created. Otherwise, a promise yielding
 * a model instance is returned.
 */
function create (method, resource, config) {
    const req = this.parseRequestConfig(method, resource, config);

    if (!req || !req.method) {
        return this;
    }

    this.promise = this.request(req);

    if (req.graft) {
        return this;
    }

    return this.promise
        .then(() => this);
}

function parseRequestConfig (method, resource, config) {
    if (!method) {
        return null;
    }

    let req = {};

    if (Array.isArray(method)) {
        if (Array.isArray(resource)) {
            req.resource = resource;
        } else if (resource === null) {
            req.resource = undefined;
        } else if (typeof resource === 'object') {
            req = resource;
        }

        req.method = method;
    } else if (typeof method === 'string') {
        if (resource === null) {
            req.resource = undefined;
        } else if (typeof resource === 'object') {
            req = resource;
        } else {
            req.resource = resource;
        }

        req.method = method;
    } else if (typeof method === 'object') {
        req = method;
    } else {
        req = config;
        req.method = method;
        req.resource = resource === null ? undefined : resource;
    }

    return req;
}

/**
 * Base functionality for API interaction.
 *
 * @arg {string} resource - The API resource for the model extending BaseModel to
 * use.
 * @arg {Object=} settings - Configuration applied to all instances of the
 * extending model.
 * @arg {boolean=} settings.cache - Cache the model data.
 *
 */
function BaseModel (resource, settings) {
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
    this.parseRequestConfig = parseRequestConfig;
    this.request = request;
    this.requestWithCache = requestWithCache;
    this.search = search;
    this.set = set;
    this.unset = unset;
    this.extend = extend;
    this.getDependentResourceCounts = getDependentResourceCounts;

    this.http = {
        get: httpGet.bind(this),
        options: httpOptions.bind(this),
        patch: httpPatch.bind(this),
        post: httpPost.bind(this),
        put: httpPut.bind(this),
        delete: httpDelete.bind(this)
    };

    this.model = {};
    this.path = this.normalizePath(resource);
    this.label = strings.get(`${resource}.LABEL`);
    this.settings = settings || {};
}

function BaseModelLoader (_$http_, _$q_, _cache_, ModelsStrings) {
    $http = _$http_;
    $q = _$q_;
    cache = _cache_;
    strings = ModelsStrings;

    return BaseModel;
}

BaseModelLoader.$inject = ['$http', '$q', 'CacheService', 'ModelsStrings'];

export default BaseModelLoader;
