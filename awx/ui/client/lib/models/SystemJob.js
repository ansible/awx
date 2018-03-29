let BaseModel;

function getStats () {
    return Promise.resolve(null);
}

function SystemJobModel (method, resource, config) {
    BaseModel.call(this, 'system_jobs');

    this.getStats = getStats.bind(this);

    this.Constructor = SystemJobModel;

    return this.create(method, resource, config);
}

function SystemJobModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return SystemJobModel;
}

SystemJobModelLoader.$inject = ['BaseModel'];

export default SystemJobModelLoader;
