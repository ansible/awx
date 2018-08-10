let $http;
let BaseModel;

function getRelaunch (params) {
    const req = {
        method: 'GET',
        url: `${this.path}${params.id}/relaunch/`
    };

    return $http(req);
}

function postRelaunch (params) {
    const req = {
        method: 'POST',
        url: `${this.path}${params.id}/relaunch/`
    };

    if (params.relaunchData) {
        req.data = params.relaunchData;
    }

    return $http(req);
}

function getCredentials (id) {
    const req = {
        method: 'GET',
        url: `${this.path}${id}/credentials/`
    };

    return $http(req);
}

function JobModel (method, resource, config) {
    BaseModel.call(this, 'jobs');

    this.Constructor = JobModel;

    this.postRelaunch = postRelaunch.bind(this);
    this.getRelaunch = getRelaunch.bind(this);
    this.getCredentials = getCredentials.bind(this);

    return this.create(method, resource, config);
}

function JobModelLoader (_$http_, _BaseModel_) {
    $http = _$http_;
    BaseModel = _BaseModel_;

    return JobModel;
}

JobModelLoader.$inject = [
    '$http',
    'BaseModel',
];

export default JobModelLoader;
