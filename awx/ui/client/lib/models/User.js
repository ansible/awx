let Base;
let $http;

function postAuthorizedTokens (params) {
    const req = {
        method: 'POST',
        url: `${this.path}${params.id}/authorized_tokens/`
    };

    if (params.payload) {
        req.data = params.payload;
    }

    return $http(req);
}

function UserModel (method, resource, config) {
    Base.call(this, 'users');

    this.Constructor = UserModel;
    this.postAuthorizedTokens = postAuthorizedTokens.bind(this);

    this.model.launch = {};

    return this.create(method, resource, config);
}

function UserModelLoader (BaseModel, _$http_) {
    Base = BaseModel;
    $http = _$http_;

    return UserModel;
}

UserModelLoader.$inject = [
    'BaseModel',
    '$http'
];

export default UserModelLoader;
