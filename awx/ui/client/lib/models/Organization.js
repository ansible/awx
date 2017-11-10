let Base;

function OrganizationModel (method, resource, config) {
    Base.call(this, 'organizations');

    this.Constructor = OrganizationModel;

    return this.create(method, resource, config);
}

function OrganizationModelLoader (BaseModel) {
    Base = BaseModel;

    return OrganizationModel;
}

OrganizationModelLoader.$inject = [
    'BaseModel'
];

export default OrganizationModelLoader;
