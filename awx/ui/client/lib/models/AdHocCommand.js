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

    return $http(req);
}

function AdHocCommandModel (method, resource, config) {
    BaseModel.call(this, 'ad_hoc_commands');

    this.Constructor = AdHocCommandModel;
    this.postRelaunch = postRelaunch.bind(this);
    this.getRelaunch = getRelaunch.bind(this);

    return this.create(method, resource, config);
}

function AdHocCommandModelLoader (_$http_, _BaseModel_) {
    $http = _$http_;
    BaseModel = _BaseModel_;

    return AdHocCommandModel;
}

AdHocCommandModelLoader.$inject = [
    '$http',
    'BaseModel',
];

export default AdHocCommandModelLoader;
