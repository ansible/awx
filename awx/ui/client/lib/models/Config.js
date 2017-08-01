let BaseModel;

function getTruncatedVersion () {
    let version;

    try {
        version = this.get('version').split('-')[0];
    } catch (err) {
        console.error(err);
    }

    return version;
}

function isOpen () {
    return this.get('license_info.license_type') === 'open';
}
  
function ConfigModel (method, resource, graft) {
    BaseModel.call(this, 'config', { cache: true });

    this.Constructor = ConfigModel;
    this.getTruncatedVersion = getTruncatedVersion;
    this.isOpen = isOpen;

    return this.create(method, resource, graft);
}

function ConfigModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return ConfigModel;
}

ConfigModelLoader.$inject = ['BaseModel'];

export default ConfigModelLoader;
