function CredentialTypesStrings (BaseString) {
    BaseString.call(this, 'credential_types');

    let t = this.t;
    let ns = this.credential_types;

    ns.deleteCredentialType = {
        CREDENTIAL_TYPE_IN_USE: t.s('This credential type is currently being used by one or more credentials.  Credentials that use this credential type must be deleted before the credential type can be deleted.')
    };
}

CredentialTypesStrings.$inject = ['BaseStringService'];

export default CredentialTypesStrings;
