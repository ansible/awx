function BaseModel ($http) {
    return function extend (path) {
        this.get = () => {
            let request = {
                method: 'GET',
                url: this.path
            };

            return $http(request)
                .then(response => {
                    this.model.get = response;

                    return response;
                });
        };

        this.post = data => {
            let request = {
                method: 'POST',
                url: this.path,
                data,
            };

            return $http(request)
                .then(response => {
                    this.model.post = response;

                    return response;
                });
        };

        this.options = () => {
            let request = {
                method: 'OPTIONS',
                url: this.path
            };

            return $http(request)
                .then(response => {
                    this.model.options = response;

                    return response;
                });
        };

        this.getOptions = (method, key) => {
            if (!method) {
                return this.model.options.data;
            }

            method = method.toUpperCase();

            if (method && !key) {
                return this.model.options.data.actions[method];
            }

            if (method && key) {
                return this.model.options.data.actions[method][key];
            }

            return null;
        };

        this.normalizePath = resource => {
            let version = '/api/v2/';
            
            return `${version}${resource}/`;
        };

        this.model = {};
        this.path = this.normalizePath(path);
    };
}

BaseModel.$inject = ['$http'];

export default BaseModel;
