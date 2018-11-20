let Base;
let JobTemplate;
let WorkflowJobTemplate;

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new JobTemplate(),
            params: {
                inventory: id
            }
        },
        {
            model: new WorkflowJobTemplate(),
            params: {
                inventory: id
            }
        }
    ];
}

function InventoryModel (method, resource, config) {
    Base.call(this, 'inventories');

    this.Constructor = InventoryModel;
    this.setDependentResources = setDependentResources.bind(this);

    return this.create(method, resource, config);
}

function InventoryModelLoader (BaseModel, JobTemplateModel, WorkflowJobTemplateModel) {
    Base = BaseModel;
    JobTemplate = JobTemplateModel;
    WorkflowJobTemplate = WorkflowJobTemplateModel;

    return InventoryModel;
}

InventoryModelLoader.$inject = [
    'BaseModel',
    'JobTemplateModel',
    'WorkflowJobTemplateModel',
];

export default InventoryModelLoader;
