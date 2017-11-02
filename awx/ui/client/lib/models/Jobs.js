let BaseModel;

function JobsModel (method, resource, config) {
    BaseModel.call(this, 'jobs');

    this.Constructor = JobsModel;

    return this.create(method, resource, config);
}

function JobsModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return JobsModel;
}

JobsModelLoader.$inject = ['BaseModel'];

export default JobsModelLoader;
