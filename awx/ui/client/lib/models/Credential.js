const ENCRYPTED_VALUE = '$encrypted$';

let Base;
let Project;
let JobTemplate;
let Inventory;
let InventorySource;

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
            model: new Project(),
            params: {
                credential: id
            }
        },
        {
            model: new JobTemplate(),
            params: {
                credential: id,
                ask_credential_on_launch: false
            }
        },
        {
            model: new Inventory(),
            params: {
                insights_credential: id
            }
        },
        {
            model: new InventorySource(),
            params: {
                credential: id
            }
        }
    ];
}

function CredentialModel (method, resource, config) {
    Base.call(this, 'credentials');

    this.Constructor = CredentialModel;
    this.createFormSchema = createFormSchema.bind(this);
    this.assignInputGroupValues = assignInputGroupValues.bind(this);
    this.setDependentResources = setDependentResources.bind(this);

    return this.create(method, resource, config);
}

function CredentialModelLoader (
    BaseModel,
    ProjectModel,
    JobTemplateModel,
    InventoryModel,
    InventorySourceModel
) {
    Base = BaseModel;
    Project = ProjectModel;
    JobTemplate = JobTemplateModel;
    Inventory = InventoryModel;
    InventorySource = InventorySourceModel;

    return CredentialModel;
}

CredentialModelLoader.$inject = [
    'BaseModel',
    'ProjectModel',
    'JobTemplateModel',
    'InventoryModel',
    'InventorySourceModel'
];

export default CredentialModelLoader;
