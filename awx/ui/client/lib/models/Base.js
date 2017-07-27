let $http;
let $q;

function request (method, resource) {
    if (Array.isArray(method) && Array.isArray(resource)) {
        let promises = method.map((value, i) => this.http[value](resource[i]));

        return $q.all(promises);
    }
    
    return this.http[method](resource);
}

function search (params, config) {
    let req = {
        method: 'GET',
        url: this.path,
        params
    };

    return $http(req)
        .then(res => {
            if (!res.data.count) {
                return false;
            }

            if (config.unique) {
                if (res.data.count !== 1) {
                    return false;
                }

                this.model.GET = res.data.results[0];
            } else {
                this.model.GET = res.data;
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

function graft (id) {
    let item = this.get('results').filter(result => result.id === id);

    item = item ? item[0] : undefined;

    if (!item) {
        return undefined;
    }

    return new this.Constructor('get', item, true);
}

function create (method, resource, graft) {
    if (!method) {
        return this;
    }

    this.promise = this.request(method, resource);

    if (graft) {
        return this;
    }

    return this.promise
        .then(() => this);
}

function BaseModel (path) {
    this.create = create;
    this.find = find;
    this.get = get;
    this.graft = graft;
    this.has = has;
    this.isEditable = isEditable;
    this.isCreatable = isCreatable;
    this.match = match;
    this.model = {};
    this.normalizePath = normalizePath;
    this.options = options;
    this.request = request;
    this.search = search;
    this.set = set;
    this.unset = unset;

    this.http = {
        get: httpGet.bind(this),
        options: httpOptions.bind(this),
        post: httpPost.bind(this),
        put: httpPut.bind(this),
    };

    this.path = this.normalizePath(path);
};

function BaseModelLoader (_$http_, _$q_) {
    $http = _$http_;
    $q = _$q_;

    return BaseModel;
}

BaseModelLoader.$inject = ['$http', '$q'];

export default BaseModelLoader;
