const ENCRYPTED_VALUE = '$encrypted$';

let BaseModel;
let ProjectModel;
let JobTemplateModel;
let InventoryModel;
let InventorySourceModel;
let ModelsStrings;

function createFormSchema (method, config) {
    if (!config) {
        config = method;
        method = 'GET';
    }

    const schema = Object.assign({}, this.options(`actions.${method.toUpperCase()}`));

    if (config && config.omit) {
        config.omit.forEach(key => delete schema[key]);
    }

    Object.keys(schema).forEach(key => {
        schema[key].id = key;

        if (this.has(key)) {
            schema[key]._value = this.get(key);
        }
    });

    return schema;
}

function assignInputGroupValues (inputs) {
    if (!inputs) {
        return [];
    }

    return inputs.map(input => {
        const value = this.get(`inputs.${input.id}`);

        input._value = value;
        input._encrypted = value === ENCRYPTED_VALUE;

        return input;
    });
}

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new ProjectModel(),
            params: {
                credential: id
            }
        },
        {
            model: new JobTemplateModel(),
            params: {
                credential: id,
                ask_credential_on_launch: false
            }
        },
        {
            model: new InventoryModel(),
            params: {
                insights_credential: id
            }
        },
        {
            model: new InventorySourceModel(),
            params: {
                credential: id
            }
        }
    ];
}

function CredentialModel (method, resource, graft) {
    BaseModel.call(this, 'credentials');

    this.Constructor = CredentialModel;
    this.createFormSchema = createFormSchema.bind(this);
    this.assignInputGroupValues = assignInputGroupValues.bind(this);
    this.setDependentResources = setDependentResources.bind(this);
    this.label = ModelsStrings.get('labels.CREDENTIAL');

    return this.create(method, resource, graft);
}

function CredentialModelLoader (
    _BaseModel_,
    _ProjectModel_,
    _JobTemplateModel_,
    _InventoryModel_,
    _InventorySourceModel_,
    _ModelsStrings_
) {
    BaseModel = _BaseModel_;
    ProjectModel = _ProjectModel_;
    JobTemplateModel = _JobTemplateModel_;
    InventoryModel = _InventoryModel_;
    InventorySourceModel = _InventorySourceModel_;
    ModelsStrings = _ModelsStrings_;

    return CredentialModel;
}

CredentialModelLoader.$inject = [
    'BaseModel',
    'ProjectModel',
    'JobTemplateModel',
    'InventoryModel',
    'InventorySourceModel',
    'ModelsStrings'
];

export default CredentialModelLoader;
