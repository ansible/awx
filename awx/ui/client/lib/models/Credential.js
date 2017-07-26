const ENCRYPTED_VALUE = '$encrypted$';

let BaseModel;

function createFormSchema (method, config) {
    let schema = Object.assign({}, this.options(`actions.${method.toUpperCase()}`));

    if (config && config.omit) {
        config.omit.forEach(key => {
            delete schema[key];
        });
    }

    for (let key in schema) {
        schema[key].id = key;

        if (method === 'put') {
            schema[key]._value = this.get(key);
        }
    }

    return schema;
}

function assignInputGroupValues (inputs) {
    return inputs.map(input => {
        let value = this.get(`inputs.${input.id}`);

        input._value = value;
        input._encrypted = value === ENCRYPTED_VALUE;

        return input;
    });
}

function clearTypeInputs () {
    delete this.model.GET.inputs;
}

function CredentialModel (method, resource, graft) {
    BaseModel.call(this, 'credentials');

    this.Constructor = CredentialModel;
    this.createFormSchema = createFormSchema.bind(this);
    this.assignInputGroupValues = assignInputGroupValues.bind(this);
    this.clearTypeInputs = clearTypeInputs.bind(this);

    return this.create(method, resource, graft);
}

function CredentialModelLoader (_BaseModel_ ) {
    BaseModel = _BaseModel_;

    return CredentialModel;
}

CredentialModelLoader.$inject = ['BaseModel'];

export default CredentialModelLoader;
