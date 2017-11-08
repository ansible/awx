let BaseModel;
let JobTemplateModel;
let WorkflowJobTemplateNodeModel;
let InventorySourceModel;
let ModelsStrings;

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new JobTemplateModel(),
            params: {
                project: id
            }
        },
        {
            model: new WorkflowJobTemplateNodeModel(),
            params: {
                unified_job_template: id
            }
        },
        {
            model: new InventorySourceModel(),
            params: {
                source_project: id
            }
        }
    ];
}

function ProjectModel (method, resource, graft) {
    BaseModel.call(this, 'projects');

    this.Constructor = ProjectModel;
    this.setDependentResources = setDependentResources.bind(this);
    this.label = ModelsStrings.get('labels.PROJECT');

    return this.create(method, resource, graft);
}

function ProjectModelLoader (
    _BaseModel_,
    _JobTemplateModel_,
    _WorkflowJobTemplateNodeModel_,
    _InventorySourceModel_,
    _ModelsStrings_
) {
    BaseModel = _BaseModel_;
    JobTemplateModel = _JobTemplateModel_;
    WorkflowJobTemplateNodeModel = _WorkflowJobTemplateNodeModel_;
    InventorySourceModel = _InventorySourceModel_;
    ModelsStrings = _ModelsStrings_;

    return ProjectModel;
}

ProjectModelLoader.$inject = [
    'BaseModel',
    'JobTemplateModel',
    'WorkflowJobTemplateNodeModel',
    'InventorySourceModel',
    'ModelsStrings'
];

export default ProjectModelLoader;
