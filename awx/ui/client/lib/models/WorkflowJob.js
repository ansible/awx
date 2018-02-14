let Base;

function WorkflowJobModel (method, resource, config) {
    Base.call(this, 'workflow_jobs');

    this.Constructor = WorkflowJobModel;

    return this.create(method, resource, config);
}

function WorkflowJobModelLoader (BaseModel) {
    Base = BaseModel;

    return WorkflowJobModel;
}

WorkflowJobModelLoader.$inject = [
    'BaseModel'
];

export default WorkflowJobModelLoader;
