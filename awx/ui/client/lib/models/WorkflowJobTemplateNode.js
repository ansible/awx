let BaseModel;
let ModelsStrings;

function WorkflowJobTemplateNodeModel (method, resource, graft) {
    BaseModel.call(this, 'workflow_job_template_nodes');

    this.Constructor = WorkflowJobTemplateNodeModel;
    this.label = ModelsStrings.get('labels.WORKFLOW_JOB_TEMPLATE_NODE');

    return this.create(method, resource, graft);
}

function WorkflowJobTemplateNodeModelLoader (
    _BaseModel_,
    _ModelsStrings_
) {
    BaseModel = _BaseModel_;
    ModelsStrings = _ModelsStrings_;

    return WorkflowJobTemplateNodeModel;
}

WorkflowJobTemplateNodeModelLoader.$inject = [
    'BaseModel',
    'ModelsStrings'
];

export default WorkflowJobTemplateNodeModelLoader;
