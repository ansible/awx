let Base;

function WorkflowJobTemplateNodeModel (method, resource, config) {
    Base.call(this, 'workflow_job_template_nodes');

    this.Constructor = WorkflowJobTemplateNodeModel;

    return this.create(method, resource, config);
}

function WorkflowJobTemplateNodeModelLoader (BaseModel) {
    Base = BaseModel;

    return WorkflowJobTemplateNodeModel;
}

WorkflowJobTemplateNodeModelLoader.$inject = [
    'BaseModel'
];

export default WorkflowJobTemplateNodeModelLoader;
