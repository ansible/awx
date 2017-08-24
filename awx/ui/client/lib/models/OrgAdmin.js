let BaseModel;

function OrgAdminModel (method, resource, graft) {
    BaseModel.call(this, {path: 'users', subPath: 'admin_of_organizations'});

    this.Constructor = OrgAdminModel;

    return this.create(method, resource, graft);
}

function OrgAdminModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return OrgAdminModel;
}

OrgAdminModelLoader.$inject = ['BaseModel'];

export default OrgAdminModelLoader;
