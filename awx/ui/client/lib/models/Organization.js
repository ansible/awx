let Base;
let strings;

function OrganizationModel (method, resource, config) {
    Base.call(this, 'organizations');

    this.Constructor = OrganizationModel;
    this.label = strings.get('labels.ORGANIZATION');

    return this.create(method, resource, config);
}

function OrganizationModelLoader (
    BaseModel,
    ModelsStrings
) {
    Base = BaseModel;
    strings = ModelsStrings;

    return OrganizationModel;
}

OrganizationModelLoader.$inject = [
    'BaseModel',
    'ModelsStrings'
];

export default OrganizationModelLoader;
