let $resource;

function get() {
    return $resource(this.path).get().$promise
        .then(response => {
            this.model.data = response;
        });
}

function options () {
    let actions = {
        options: {    
            method: 'OPTIONS'
        }
    };

    return $resource(this.path, null, actions).options().$promise
        .then(response => {
            this.model.options = response;
        });
}

function getPostOptions (name) {
    return this.model.options.actions.POST[name];
}

function normalizePath (resource) {
    let version = '/api/v2/';
    
    return `${version}${resource}/`;
}

function BaseModel (_$resource_) {
    $resource = _$resource_;

    return function extend (path) {
        this.get = get;
        this.options = options;
        this.getPostOptions = getPostOptions;
        this.normalizePath = normalizePath;

        this.model = {};
        this.path = this.normalizePath(path);
    };
}

BaseModel.$inject = ['$resource'];

export default BaseModel;
