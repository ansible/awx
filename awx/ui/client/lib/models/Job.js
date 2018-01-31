let Base;

function JobModel (method, resource, config) {
    Base.call(this, 'jobs');

    this.Constructor = JobModel;

    return this.create(method, resource, config);
}

function JobModelLoader (BaseModel) {
    Base = BaseModel;

    return JobModel;
}

JobModelLoader.$inject = [
    'BaseModel'
];

export default JobModelLoader;
