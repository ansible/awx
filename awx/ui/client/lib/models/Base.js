let $resource;

function options () {
    return this.model.query().$promise
        .then(response => {
            this.response = response;
            this.data = this.response.results;
        });
}

function get () {
    return $resource(this.path).get().$promise
        .then(response => {
            this.response = response;
            this.data = this.response.results;
        });
}

function normalizePath (resource) {
    let version = '/api/v2/';
    
    return `${version}${resource}/`;
}

function Base (_$resource_) {
    $resource = _$resource_;

    this.options = options;
    this.get = get;
    this.normalizePath = normalizePath;
}

Base.$inject = ['$resource'];

export default Base;
