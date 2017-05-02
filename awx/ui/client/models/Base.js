function get () {
    return this.model.get().$promise
        .then(response => {
            this.response = response;
            this.data = this.response.results;
        });
}

function normalizePath (resource) {
    let version = '/api/v2/';
    
    return `${version}${resource}/`;
}

function Base ($resource) {
    return (resource, params, actions) => {
        let path = normalizePath(resource);

        return {
            data: null,
            response: null,
            model: $resource(path, params, actions),
            get
        };
    };
}

Base.$inject = ['$resource'];

export default Base;
