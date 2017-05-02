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

function CredentialType (Base) {
    let base = Base('credential_types');

    return Object.assign(base, {
        categorizeByKind
    });
}

CredentialType.$inject = ['Base'];

export default CredentialType;
