let Base;

function setDependentResources () {
    this.dependentResources = [];
}

function TokenModel (method, resource, config) {
    Base.call(this, 'tokens');

    this.Constructor = TokenModel;
    this.setDependentResources = setDependentResources.bind(this);

    return this.create(method, resource, config);
}

function TokenModelLoader (BaseModel) {
    Base = BaseModel;

    return TokenModel;
}

TokenModelLoader.$inject = [
    'BaseModel',
];

export default TokenModelLoader;
