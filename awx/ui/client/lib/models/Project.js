let Base;
let JobTemplate;
let WorkflowJobTemplateNode;
let InventorySource;
let $http;

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

function getUpdate (id) {
    const req = {
        method: 'GET',
        url: `${this.path}${id}/update/`
    };

    return $http(req);
}

function postUpdate (id) {
    const req = {
        method: 'POST',
        url: `${this.path}${id}/update/`
    };

    return $http(req);
}

function ProjectModel (method, resource, config) {
    Base.call(this, 'projects');

    this.Constructor = ProjectModel;
    this.setDependentResources = setDependentResources.bind(this);
    this.getUpdate = getUpdate.bind(this);
    this.postUpdate = postUpdate.bind(this);

    return this.create(method, resource, config);
}

function ProjectModelLoader (
    BaseModel,
    JobTemplateModel,
    WorkflowJobTemplateNodeModel,
    InventorySourceModel,
    _$http_
) {
    Base = BaseModel;
    JobTemplate = JobTemplateModel;
    WorkflowJobTemplateNode = WorkflowJobTemplateNodeModel;
    InventorySource = InventorySourceModel;
    $http = _$http_;

    return ProjectModel;
}

ProjectModelLoader.$inject = [
    'BaseModel',
    'JobTemplateModel',
    'WorkflowJobTemplateNodeModel',
    'InventorySourceModel',
    '$http'
];

export default ProjectModelLoader;
