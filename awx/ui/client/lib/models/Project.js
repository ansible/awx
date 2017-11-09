let Base;
let JobTemplate;
let WorkflowJobTemplateNode;
let InventorySource;
let strings;

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new JobTemplate(),
            params: {
                project: id
            }
        },
        {
            model: new WorkflowJobTemplateNode(),
            params: {
                unified_job_template: id
            }
        },
        {
            model: new InventorySource(),
            params: {
                source_project: id
            }
        }
    ];
}

function ProjectModel (method, resource, config) {
    Base.call(this, 'projects');

    this.Constructor = ProjectModel;
    this.setDependentResources = setDependentResources.bind(this);
    this.label = strings.get('labels.PROJECT');

    return this.create(method, resource, config);
}

function ProjectModelLoader (
    BaseModel,
    JobTemplateModel,
    WorkflowJobTemplateNodeModel,
    InventorySourceModel,
    ModelsStrings
) {
    Base = BaseModel;
    JobTemplate = JobTemplateModel;
    WorkflowJobTemplateNode = WorkflowJobTemplateNodeModel;
    InventorySource = InventorySourceModel;
    strings = ModelsStrings;

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
