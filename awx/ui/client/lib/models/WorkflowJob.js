let Base;
let $http;

function postRelaunch (params) {
    const req = {
        method: 'POST',
        url: `${this.path}${params.id}/relaunch/`
    };

    return $http(req);
}

function WorkflowJobModel (method, resource, config) {
    Base.call(this, 'workflow_jobs');

    this.Constructor = WorkflowJobModel;
    this.postRelaunch = postRelaunch.bind(this);

    return this.create(method, resource, config);
}

function WorkflowJobModelLoader (BaseModel, _$http_) {
    Base = BaseModel;
    $http = _$http_;

    return WorkflowJobModel;
}

WorkflowJobModelLoader.$inject = [
    'BaseModel',
    '$http'
];

export default WorkflowJobModelLoader;
