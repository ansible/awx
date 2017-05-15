let $resource;

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

function get () {
    return $resource(this.path).get().$promise
        .then(response => {
            this.model.data = response;
        });
}

function getPostOptions (name) {
    return this.model.options.actions.POST[name];
}

function normalizePath (resource) {
    let version = '/api/v2/';
    
    return `${version}${resource}/`;
}

function Base (_$resource_) {
    $resource = _$resource_;

    return () => ({
        model: {},
        get,
        options,
        getPostOptions,
        normalizePath
    });
}

Base.$inject = ['$resource'];

export default Base;
