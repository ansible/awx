let BaseModel;

function OrganizationModel (method) {
    BaseModel.call(this, 'organizations');

    return this.request(method)
        .then(() => this);
}

function OrganizationModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return OrganizationModel;
}

OrganizationModelLoader.$inject = ['BaseModel'];

export default OrganizationModelLoader;
