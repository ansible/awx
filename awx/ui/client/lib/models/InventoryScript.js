let Base;
let InventorySource;
let strings;

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
    this.label = strings.get('labels.INVENTORY_SCRIPT');

    return this.create(method, resource, config);
}

function InventoryScriptModelLoader (
    BaseModel,
    InventorySourceModel,
    ModelsStrings
) {
    Base = BaseModel;
    InventorySource = InventorySourceModel;
    strings = ModelsStrings;

    return InventoryScriptModel;
}

InventoryScriptModelLoader.$inject = [
    'BaseModel',
    'InventorySourceModel',
    'ModelsStrings'
];

export default InventoryScriptModelLoader;
