let Base;
let JobTemplate;
let strings;

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new JobTemplate(),
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
    this.label = strings.get('labels.INVENTORY');

    return this.create(method, resource, config);
}

function InventoryModelLoader (
    BaseModel,
    JobTemplateModel,
    ModelsStrings
) {
    Base = BaseModel;
    JobTemplate = JobTemplateModel;
    strings = ModelsStrings;

    return InventoryModel;
}

InventoryModelLoader.$inject = [
    'BaseModel',
    'JobTemplateModel',
    'ModelsStrings'
];

export default InventoryModelLoader;
