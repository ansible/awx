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

function getStats () {
    if (!this.has('GET', 'id')) {
        return Promise.reject(new Error('No property, id, exists'));
    }

    if (!this.has('GET', 'related.job_events')) {
        return Promise.reject(new Error('No related property, job_events, exists'));
    }

    const req = {
        method: 'GET',
        url: `${this.path}${this.get('id')}/job_events/`,
        params: { event: 'playbook_on_stats' },
    };

    return $http(req)
        .then(({ data }) => {
            if (data.results.length > 0) {
                return data.results[0];
            }

            return null;
        });
}

function JobModel (method, resource, config) {
    BaseModel.call(this, 'jobs');

    this.Constructor = JobModel;

    this.postRelaunch = postRelaunch.bind(this);
    this.getRelaunch = getRelaunch.bind(this);
    this.getStats = getStats.bind(this);

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
