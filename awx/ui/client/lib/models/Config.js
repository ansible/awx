let $log;
let Base;

function getTruncatedVersion () {
    let version;

    try {
        [version] = this.get('version').split('-');
    } catch (err) {
        $log.error(err);
    }

    return version;
}

function isOpen () {
    return this.get('license_info.license_type') === 'open';
}

function ConfigModel (method, resource, config) {
    Base.call(this, 'config', { cache: true });

    this.Constructor = ConfigModel;
    this.getTruncatedVersion = getTruncatedVersion;
    this.isOpen = isOpen;

    return this.create(method, resource, config);
}

function ConfigModelLoader (BaseModel, _$log_) {
    Base = BaseModel;
    $log = _$log_;

    return ConfigModel;
}

ConfigModelLoader.$inject = ['BaseModel', '$log'];

export default ConfigModelLoader;
