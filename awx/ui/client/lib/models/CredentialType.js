function CredentialTypeModel (BaseModel) {
    BaseModel.call(this, 'credential_types');

    this.categorizeByKind = () => {
        let group = {};

        this.model.get.data.results.forEach(result => {
            group[result.kind] = group[result.kind] || [];
            group[result.kind].push(result);
        });

        return Object.keys(group).map(category => ({
            data: group[category],
            category
        }));
    };

    this.getTypeFromName = name => {
        let type = this.model.get.data.results.filter(result => result.name === name);

        if (!type.length) {
            return null;
        }

        return this.mergeInputProperties(type[0]);
    };

    this.mergeInputProperties = type => {
        return type.inputs.fields.map(field => {
            if (!type.inputs.required || type.inputs.required.indexOf(field.id) === -1) {
                field.required = false;
            } else {
                field.required = true;
            }

            return field;
        });
    };

    this.getResults = () => {
        return this.model.get.data.results;
    };
}

CredentialTypeModel.$inject = ['BaseModel'];

export default CredentialTypeModel;
