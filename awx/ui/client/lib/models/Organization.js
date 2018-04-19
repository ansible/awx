let Base;
let Credential;

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new Credential(),
            params: {
                organization: id
            }
        }
    ];
}

function OrganizationModel (method, resource, config) {
    Base.call(this, 'organizations');

    this.Constructor = OrganizationModel;
    this.setDependentResources = setDependentResources.bind(this);

    return this.create(method, resource, config);
}

function OrganizationModelLoader (BaseModel, CredentialModel) {
    Base = BaseModel;
    Credential = CredentialModel;

    return OrganizationModel;
}

OrganizationModelLoader.$inject = [
    'BaseModel',
    'CredentialModel'
];

export default OrganizationModelLoader;
