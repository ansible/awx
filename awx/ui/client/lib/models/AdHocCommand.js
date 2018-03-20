let Base;
let $http;

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

    return $http(req);
}

function AdHocCommandModel (method, resource, config) {
    Base.call(this, 'ad_hoc_commands');

    this.Constructor = AdHocCommandModel;
    this.postRelaunch = postRelaunch.bind(this);
    this.getRelaunch = getRelaunch.bind(this);

    return this.create(method, resource, config);
}

function AdHocCommandModelLoader (BaseModel, _$http_) {
    Base = BaseModel;
    $http = _$http_;

    return AdHocCommandModel;
}

AdHocCommandModelLoader.$inject = [
    'BaseModel',
    '$http'
];

export default AdHocCommandModelLoader;
