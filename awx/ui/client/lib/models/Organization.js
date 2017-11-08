let BaseModel;
let ModelsStrings;

function OrganizationModel (method, resource, graft) {
    BaseModel.call(this, 'organizations');

    this.Constructor = OrganizationModel;
    this.label = ModelsStrings.get('labels.ORGANIZATION');

    return this.create(method, resource, graft);
}

function OrganizationModelLoader (
    _BaseModel_,
    _ModelsStrings_
) {
    BaseModel = _BaseModel_;
    ModelsStrings = _ModelsStrings_;

    return OrganizationModel;
}

OrganizationModelLoader.$inject = [
    'BaseModel',
    'ModelsStrings'
];

export default OrganizationModelLoader;
