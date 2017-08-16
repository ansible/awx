let BaseModel;

function OrganizationModel (method, resource, graft) {
    BaseModel.call(this, 'organizations');

    this.Constructor = OrganizationModel;

    return this.create(method, resource, graft);
}

function OrganizationModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return OrganizationModel;
}

OrganizationModelLoader.$inject = ['BaseModel'];

export default OrganizationModelLoader;
