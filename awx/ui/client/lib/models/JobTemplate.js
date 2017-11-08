let BaseModel;
let WorkflowJobTemplateNodeModel;
let ModelsStrings;

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new WorkflowJobTemplateNodeModel(),
            params: {
                unified_job_template: id
            }
        }
    ];
}

function JobTemplateModel (method, resource, graft) {
    BaseModel.call(this, 'job_templates');

    this.Constructor = JobTemplateModel;
    this.setDependentResources = setDependentResources.bind(this);
    this.label = ModelsStrings.get('labels.JOB_TEMPLATE');

    return this.create(method, resource, graft);
}

function JobTemplateModelLoader (
    _BaseModel_,
    _WorkflowJobTemplateNodeModel_,
    _ModelsStrings_
) {
    BaseModel = _BaseModel_;
    WorkflowJobTemplateNodeModel = _WorkflowJobTemplateNodeModel_;
    ModelsStrings = _ModelsStrings_;

    return JobTemplateModel;
}

JobTemplateModelLoader.$inject = [
    'BaseModel',
    'WorkflowJobTemplateNodeModel',
    'ModelsStrings'
];

export default JobTemplateModelLoader;
