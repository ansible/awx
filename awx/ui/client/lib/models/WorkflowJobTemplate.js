let Base;

function WorkflowJobTemplateModel (method, resource, config) {
    Base.call(this, 'workflow_job_templates');

    this.Constructor = WorkflowJobTemplateModel;

    return this.create(method, resource, config);
}

function WorkflowJobTemplateModelLoader (BaseModel) {
    Base = BaseModel;

    return WorkflowJobTemplateModel;
}

WorkflowJobTemplateModelLoader.$inject = [
    'BaseModel'
];

export default WorkflowJobTemplateModelLoader;
