/* eslint camelcase: 0 */
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

    // Custom credentials can have input fields named 'name', 'organization',
    // 'description', etc. Underscore these variables to make collisions
    // less likely to occur.
    schema._name = schema.name;
    schema._organization = schema.organization;
    schema._description = schema.description;
    delete schema.name;
    delete schema.organization;
    delete schema.description;

    return schema;
}

function assignInputGroupValues (apiConfig, credentialType, sourceCredentials) {
    let inputs = credentialType.get('inputs.fields');

    if (!inputs) {
        return [];
    }

    if (this.has('credential_type')) {
        if (credentialType.get('id') !== this.get('credential_type')) {
            inputs.forEach(field => {
                field.tagMode = this.isEditable() && credentialType.get('kind') !== 'external';
            });
            return inputs;
        }
    }

    inputs = inputs.map(input => {
        const value = this.get(`inputs.${input.id}`);

        input._value = value;
        input._encrypted = value === ENCRYPTED_VALUE;

        return input;
    });

    if (credentialType.get('namespace') === 'ssh') {
        const become = inputs.find((field) => field.id === 'become_method');
        become._isDynamic = true;
        become._choices = Array.from(apiConfig.become_methods, method => method[0]);
        // Add the value to the choices if it doesn't exist in the preset list
        if (become._value && become._value !== '') {
            const optionMatches = become._choices
                .findIndex((option) => option === become._value);
            if (optionMatches === -1) {
                become._choices.push(become._value);
            }
        }
    }

    const linkedFieldNames = (this.get('related.input_sources.results') || [])
        .map(({ input_field_name }) => input_field_name);

    inputs = inputs.map((field) => {
        field.tagMode = this.isEditable() && credentialType.get('kind') !== 'external';
        if (linkedFieldNames.includes(field.id)) {
            field.tagMode = true;
            field.asTag = true;
            const { summary_fields } = this.get('related.input_sources.results')
                .find(({ input_field_name }) => input_field_name === field.id);
            field._tagValue = summary_fields.source_credential.name;

            const { source_credential: { id } } = summary_fields;
            const src = sourceCredentials.data.results.find(obj => obj.id === id);
            const canRemove = _.get(src, ['summary_fields', 'user_capabilities', 'delete'], false);

            if (!canRemove) {
                field._disabled = true;
            }
        }

        return field;
    });

    return inputs;
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
                credentials__id: id,
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
                credentials__id: id
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
