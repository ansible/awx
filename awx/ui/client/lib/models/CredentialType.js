let Base;
let Credential;
let strings;

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

function mergeInputProperties () {
    if (!this.has('inputs.fields')) {
        return undefined;
    }

    const required = this.get('inputs.required');

    return this.get('inputs.fields').forEach((field, i) => {
        if (!required || required.indexOf(field.id) === -1) {
            this.set(`inputs.fields[${i}].required`, false);
        } else {
            this.set(`inputs.fields[${i}].required`, true);
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
    this.label = strings.get('labels.CREDENTIAL_TYPE');

    return this.create(method, resource, config);
}

function CredentialTypeModelLoader (
    BaseModel,
    CredentialModel,
    ModelsStrings
) {
    Base = BaseModel;
    Credential = CredentialModel;
    strings = ModelsStrings;

    return CredentialTypeModel;
}

CredentialTypeModelLoader.$inject = [
    'BaseModel',
    'CredentialModel',
    'ModelsStrings'
];

export default CredentialTypeModelLoader;
