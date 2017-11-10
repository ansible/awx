function CredentialTypesStrings (BaseString) {
    BaseString.call(this, 'credential_types');

    let t = this.t;
    let ns = this.credential_types;

    ns.deleteCredentialType = {
        CONFIRM: t.s('Are you sure you want to delete this credential type?'),
        CREDENTIAL_TYPE_IN_USE: t.s('This credential type is currently being used by one or more credentials.  Credentials that use this credential type must be deleted before the credential type can be deleted.')
    };
}

CredentialTypesStrings.$inject = ['BaseStringService'];

export default CredentialTypesStrings;
