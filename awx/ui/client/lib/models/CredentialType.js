function categorizeByKind () {
    let group = {};

    this.model.data.results.forEach(result => {
        group[result.kind] = group[result.kind] || [];
        group[result.kind].push(result);
    });

    return Object.keys(group).map(category => ({
        data: group[category],
        category
    }));
}

function getTypeFromName (name) {
    let type = this.model.data.results.filter(result => result.name === name);

    return type.length ? type[0] : null;
}

function CredentialType (BaseModel) {
    Object.assign(this, BaseModel());

    this.path = this.normalizePath('credential_types');

    this.categorizeByKind = categorizeByKind;
    this.getTypeFromName = getTypeFromName;
}

CredentialType.$inject = ['BaseModel'];

export default CredentialType;
