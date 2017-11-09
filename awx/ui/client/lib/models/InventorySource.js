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

function InventorySourceModel (method, resource, config) {
    Base.call(this, 'inventory_sources');

    this.Constructor = InventorySourceModel;
    this.label = strings.get('labels.INVENTORY_SOURCE');
    this.setDependentResources = setDependentResources.bind(this);

    return this.create(method, resource, config);
}

function InventorySourceModelLoader (
    BaseModel,
    WorkflowJobTemplateNodeModel,
    ModelsStrings
) {
    Base = BaseModel;
    WorkflowJobTemplateNode = WorkflowJobTemplateNodeModel;
    strings = ModelsStrings;

    return InventorySourceModel;
}

InventorySourceModelLoader.$inject = [
    'BaseModel',
    'WorkflowJobTemplateNodeModel',
    'ModelsStrings'
];

export default InventorySourceModelLoader;
