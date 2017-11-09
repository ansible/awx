let Base;
let strings;

function WorkflowJobTemplateNodeModel (method, resource, config) {
    Base.call(this, 'workflow_job_template_nodes');

    this.Constructor = WorkflowJobTemplateNodeModel;
    this.label = strings.get('labels.WORKFLOW_JOB_TEMPLATE_NODE');

    return this.create(method, resource, config);
}

function WorkflowJobTemplateNodeModelLoader (
    BaseModel,
    ModelsStrings
) {
    Base = BaseModel;
    strings = ModelsStrings;

    return WorkflowJobTemplateNodeModel;
}

WorkflowJobTemplateNodeModelLoader.$inject = [
    'BaseModel',
    'ModelsStrings'
];

export default WorkflowJobTemplateNodeModelLoader;
