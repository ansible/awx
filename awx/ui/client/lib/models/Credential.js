function CredentialModel (BaseModel, CredentialTypeModel) {
    BaseModel.call(this, 'credentials');
    
    this.createFormSchema = (type, config) => {
        let schema = Object.assign({}, this.getOptions(type));

        if (config && config.omit) {
            config.omit.forEach(key => {
                delete schema[key];
            });
        }

        for (let key in schema) {
            schema[key].id = key;
        }

        return schema;
    };
}

CredentialModel.$inject = ['BaseModel', 'CredentialTypeModel'];

export default CredentialModel;
