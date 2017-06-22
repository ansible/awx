let $http;
let $q;

function request (method, resource) {
    if (Array.isArray(method) && Array.isArray(resource)) {
        let promises = method.map((value, i) => this.http[value](resource[i]));

        return $q.all(promises);
    }
    
    return this.http[method](resource);
}

function httpGet (resource) {
    let req = {
        method: 'GET',
        url: this.path
    };

    if (typeof resource === 'object') {
        this.model[this.method] = resource;

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

function normalizePath (resource) {
    let version = '/api/v2/';
    
    return `${version}${resource}/`;
}

function getById (id) {
    let item = this.get('results').filter(result => result.id === id);

    return item ? item[0] : undefined;
}

function BaseModel (path) {
    this.model = {};
    this.get = get;
    this.options = options;
    this.find = find;
    this.normalizePath = normalizePath;
    this.getById = getById;
    this.request = request;
    this.http = {
        get: httpGet.bind(this),
        options: httpOptions.bind(this),
        post: httpPost.bind(this),
        put: httpPut.bind(this)
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
