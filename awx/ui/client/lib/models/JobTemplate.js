let Base;
let WorkflowJobTemplateNode;
let strings;

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
    this.label = strings.get('labels.JOB_TEMPLATE');

    return this.create(method, resource, config);
}

function JobTemplateModelLoader (
    BaseModel,
    WorkflowJobTemplateNodeModel,
    ModelsStrings
) {
    Base = BaseModel;
    WorkflowJobTemplateNode = WorkflowJobTemplateNodeModel;
    strings = ModelsStrings;

    return JobTemplateModel;
}

JobTemplateModelLoader.$inject = [
    'BaseModel',
    'WorkflowJobTemplateNodeModel',
    'ModelsStrings'
];

export default JobTemplateModelLoader;
