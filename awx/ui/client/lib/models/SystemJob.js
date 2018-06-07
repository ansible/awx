let BaseModel;

function SystemJobModel (method, resource, config) {
    BaseModel.call(this, 'system_jobs');

    this.Constructor = SystemJobModel;

    return this.create(method, resource, config);
}

function SystemJobModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return SystemJobModel;
}

SystemJobModelLoader.$inject = ['BaseModel'];

export default SystemJobModelLoader;
