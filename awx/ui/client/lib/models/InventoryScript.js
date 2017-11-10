let Base;
let InventorySource;

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new InventorySource(),
            params: {
                source_script: id
            }
        }
    ];
}

function InventoryScriptModel (method, resource, config) {
    Base.call(this, 'inventory_scripts');

    this.Constructor = InventoryScriptModel;
    this.setDependentResources = setDependentResources.bind(this);

    return this.create(method, resource, config);
}

function InventoryScriptModelLoader (BaseModel, InventorySourceModel) {
    Base = BaseModel;
    InventorySource = InventorySourceModel;

    return InventoryScriptModel;
}

InventoryScriptModelLoader.$inject = [
    'BaseModel',
    'InventorySourceModel'
];

export default InventoryScriptModelLoader;
