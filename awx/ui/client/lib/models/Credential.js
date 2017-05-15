function Credential (BaseModel) {
    Object.assign(this, BaseModel());

    this.path = this.normalizePath('credentials');
}

Credential.$inject = ['BaseModel'];

export default Credential;
