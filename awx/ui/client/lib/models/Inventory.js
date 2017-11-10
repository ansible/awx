let Base;
let JobTemplate;

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

    return this.create(method, resource, config);
}

function InventoryModelLoader (BaseModel, JobTemplateModel) {
    Base = BaseModel;
    JobTemplate = JobTemplateModel;

    return InventoryModel;
}

InventoryModelLoader.$inject = [
    'BaseModel',
    'JobTemplateModel'
];

export default InventoryModelLoader;
