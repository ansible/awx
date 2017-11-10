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

function InventorySourceModel (method, resource, config) {
    Base.call(this, 'inventory_sources');

    this.Constructor = InventorySourceModel;
    this.setDependentResources = setDependentResources.bind(this);

    return this.create(method, resource, config);
}

function InventorySourceModelLoader (
    BaseModel,
    WorkflowJobTemplateNodeModel
) {
    Base = BaseModel;
    WorkflowJobTemplateNode = WorkflowJobTemplateNodeModel;

    return InventorySourceModel;
}

InventorySourceModelLoader.$inject = [
    'BaseModel',
    'WorkflowJobTemplateNodeModel'
];

export default InventorySourceModelLoader;
