let BaseModel;

function categorizeByKind () {
    let group = {};

    this.get('results').forEach(result => {
        group[result.kind] = group[result.kind] || [];
        group[result.kind].push(result);
    });

    return Object.keys(group).map(category => ({
        data: group[category],
        category
    }));
}

function mergeInputProperties (type) {
    return type.inputs.fields.map(field => {
        if (!type.inputs.required || type.inputs.required.indexOf(field.id) === -1) {
            field.required = false;
        } else {
            field.required = true;
        }

        return field;
    });
}

function CredentialTypeModel (method, id) {
    BaseModel.call(this, 'credential_types');

    this.categorizeByKind = categorizeByKind;
    this.mergeInputProperties = mergeInputProperties;

    return this.request(method, id)
        .then(() => this);
}

function CredentialTypeModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return CredentialTypeModel;
}

CredentialTypeModelLoader.$inject = ['BaseModel'];

export default CredentialTypeModelLoader;
