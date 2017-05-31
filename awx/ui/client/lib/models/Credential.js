let BaseModel;

function createFormSchema (type, config) {
    let schema = Object.assign({}, this.get('actions.POST'));

    if (config && config.omit) {
        config.omit.forEach(key => {
            delete schema[key];
        });
    }

    for (let key in schema) {
        schema[key].id = key;
    }

    return schema;
}

function CredentialModel (method, id) {
    BaseModel.call(this, 'credentials');
    
    this.createFormSchema = createFormSchema.bind(this);

    return this.request(method, id)
        .then(() => this);
}

function CredentialModelLoader (_BaseModel_ ) {
    BaseModel = _BaseModel_;

    return CredentialModel;
}

CredentialModelLoader.$inject = ['BaseModel'];

export default CredentialModelLoader;
