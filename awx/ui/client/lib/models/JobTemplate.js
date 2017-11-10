let Base;
let WorkflowJobTemplateNode;

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new WorkflowJobTemplateNode(),
            params: {
                unified_job_template: id
            }
        }
    ];
}

function JobTemplateModel (method, resource, config) {
    Base.call(this, 'job_templates');

    this.Constructor = JobTemplateModel;
    this.setDependentResources = setDependentResources.bind(this);

    return this.create(method, resource, config);
}

function JobTemplateModelLoader (BaseModel, WorkflowJobTemplateNodeModel) {
    Base = BaseModel;
    WorkflowJobTemplateNode = WorkflowJobTemplateNodeModel;

    return JobTemplateModel;
}

JobTemplateModelLoader.$inject = [
    'BaseModel',
    'WorkflowJobTemplateNodeModel'
];

export default JobTemplateModelLoader;
