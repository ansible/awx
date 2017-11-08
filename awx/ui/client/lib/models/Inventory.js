let BaseModel;
let JobTemplateModel;
let ModelsStrings;

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new JobTemplateModel(),
            params: {
                inventory: id
            }
        }
    ];
}

function InventoryModel (method, resource, graft) {
    BaseModel.call(this, 'inventories');

    this.Constructor = InventoryModel;
    this.setDependentResources = setDependentResources.bind(this);
    this.label = ModelsStrings.get('labels.INVENTORY');

    return this.create(method, resource, graft);
}

function InventoryModelLoader (
    _BaseModel_,
    _JobTemplateModel_,
    _ModelsStrings_
) {
    BaseModel = _BaseModel_;
    JobTemplateModel = _JobTemplateModel_;
    ModelsStrings = _ModelsStrings_;

    return InventoryModel;
}

InventoryModelLoader.$inject = [
    'BaseModel',
    'JobTemplateModel',
    'ModelsStrings'
];

export default InventoryModelLoader;
