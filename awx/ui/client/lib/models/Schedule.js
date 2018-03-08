let Base;
let $http;

function postCredential (params) {
    const req = {
        method: 'POST',
        url: `${this.path}${params.id}/credentials/`
    };

    if (params.data) {
        req.data = params.data;
    }

    return $http(req);
}

function ScheduleModel (method, resource, config) {
    Base.call(this, 'schedules');

    this.Constructor = ScheduleModel;
    this.postCredential = postCredential.bind(this);

    return this.create(method, resource, config);
}

function ScheduleModelLoader (BaseModel, _$http_) {
    Base = BaseModel;
    $http = _$http_;

    return ScheduleModel;
}

ScheduleModelLoader.$inject = [
    'BaseModel',
    '$http'
];

export default ScheduleModelLoader;
