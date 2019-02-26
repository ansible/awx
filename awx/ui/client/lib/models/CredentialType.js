let Base;
let Credential;

function categorizeByKind () {
    const group = {};

    this.get('results').forEach(result => {
        group[result.kind] = group[result.kind] || [];
        group[result.kind].push(result);
    });

    return Object.keys(group).map(category => ({
        data: group[category],
        category
    }));
}

function mergeInputProperties (key = 'fields') {
    if (!this.has(`inputs.${key}`)) {
        return undefined;
    }

    const required = this.get('inputs.required');

    return this.get(`inputs.${key}`).forEach((field, i) => {
        if (!required || required.indexOf(field.id) === -1) {
            this.set(`inputs.${key}[${i}].required`, false);
        } else {
            this.set(`inputs.${key}[${i}].required`, true);
        }
    });
}

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new Credential(),
            params: {
                credential_type: id
            }
        }
    ];
}

function CredentialTypeModel (method, resource, config) {
    Base.call(this, 'credential_types');

    this.Constructor = CredentialTypeModel;
    this.categorizeByKind = categorizeByKind.bind(this);
    this.mergeInputProperties = mergeInputProperties.bind(this);
    this.setDependentResources = setDependentResources.bind(this);

    return this.create(method, resource, config);
}

function CredentialTypeModelLoader (BaseModel, CredentialModel) {
    Base = BaseModel;
    Credential = CredentialModel;

    return CredentialTypeModel;
}

CredentialTypeModelLoader.$inject = [
    'BaseModel',
    'CredentialModel'
];

export default CredentialTypeModelLoader;
