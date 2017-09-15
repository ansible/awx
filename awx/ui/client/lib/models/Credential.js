const ENCRYPTED_VALUE = '$encrypted$';

let BaseModel;

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

function CredentialModel (method, resource, graft) {
    BaseModel.call(this, 'credentials');

    this.Constructor = CredentialModel;
    this.createFormSchema = createFormSchema.bind(this);
    this.assignInputGroupValues = assignInputGroupValues.bind(this);

    return this.create(method, resource, graft);
}

function CredentialModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return CredentialModel;
}

CredentialModelLoader.$inject = ['BaseModel'];

export default CredentialModelLoader;
