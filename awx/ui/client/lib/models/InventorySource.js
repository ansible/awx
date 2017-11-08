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

function InventorySourceModel (method, resource, graft) {
    BaseModel.call(this, 'inventory_sources');

    this.Constructor = InventorySourceModel;
    this.setDependentResources = setDependentResources.bind(this);
    this.label = ModelsStrings.get('labels.INVENTORY_SOURCE');

    return this.create(method, resource, graft);
}

function InventorySourceModelLoader (
    _BaseModel_,
    _WorkflowJobTemplateNodeModel_,
    _ModelsStrings_
) {
    BaseModel = _BaseModel_;
    WorkflowJobTemplateNodeModel = _WorkflowJobTemplateNodeModel_;
    ModelsStrings = _ModelsStrings_;

    return InventorySourceModel;
}

InventorySourceModelLoader.$inject = [
    'BaseModel',
    'WorkflowJobTemplateNodeModel',
    'ModelsStrings'
];

export default InventorySourceModelLoader;
