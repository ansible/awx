let BaseModel;

function JobEventModel (method, resource, config) {
    BaseModel.call(this, 'job_events');

    this.Constructor = JobEventModel;

    return this.create(method, resource, config);
}

function JobEventModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return JobEventModel;
}

JobEventModel.$inject = ['BaseModel'];

export default JobEventModelLoader;
