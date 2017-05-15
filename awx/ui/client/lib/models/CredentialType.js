function categorizeByKind () {
    let group = {};

    this.data.forEach(result => {
        group[result.kind] = group[result.kind] || [];
        group[result.kind].push(result);
    });

    return Object.keys(group).map(category => ({
        data: group[category],
        category
    }));
}

function CredentialType (BaseModel) {
    Object.assign(this, BaseModel);

    this.path = this.normalizePath('credential_types');

    this.categorizeByKind = categorizeByKind;
}

CredentialType.$inject = ['BaseModel'];

export default CredentialType;
