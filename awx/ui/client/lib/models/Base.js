let $http;
let $q;

function request (method, ...args) {
    this.method = method.toUpperCase();

    if (typeof args[0] === 'object') {
        this.res = null;
        this.model = args[0];

        return $q.resolve();
    }

    switch (this.method) {
        case 'OPTIONS':
            return this.httpOptions(...args);    
        case 'GET':
            return this.httpGet(...args);    
        case 'POST':
            return this.httpPost(...args);    
    }
}

function httpGet (id) {
    let req = {
        method: 'GET',
        url: this.path
    };

    if (id) {
        req.url = `${this.path}/${id}`;
    }

    return $http(req)
        .then(res => {
            this.res = res;
            this.model = res.data;

            return res;
        });
}

function httpPost (data) {
    let req = {
        method: 'POST',
        url: this.path,
        data
    };

    return $http(req)
        .then(res => {
            this.res = res;
            this.model = res.data;

            return res;
        });
}

function httpOptions () {
    let req = {
        method: 'OPTIONS',
        url: this.path
    };

    return $http(req)
        .then(res => {
            this.res = res;
            this.model = res.data;

            return res;
        });
}

function get (_keys_) {
    let keys = _keys_.split('.');
    let value = this.model;

    try {
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

function BaseModel (path) {
    this.get = get;
    this.httpGet = httpGet;
    this.httpOptions = httpOptions;
    this.httpPost = httpPost;
    this.normalizePath = normalizePath;
    this.request = request;

    this.model = {};
    this.path = this.normalizePath(path);
};

function BaseModelLoader (_$http_, _$q_) {
    $http = _$http_;
    $q = _$q_;

    return BaseModel;
}

BaseModelLoader.$inject = ['$http', '$q'];

export default BaseModelLoader;
